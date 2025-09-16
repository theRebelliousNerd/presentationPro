from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from app.arango_routes import get_arango_client, ArangoResponse
from datetime import datetime

router = APIRouter(prefix="/v1/arango", tags=["arango-extras"])

class AssetRegister(BaseModel):
    presentationId: str
    category: str
    name: str
    url: str
    path: Optional[str] = None
    size: Optional[int] = None
    mime: Optional[str] = None

@router.post("/assets/register", response_model=ArangoResponse)
async def assets_register(body: AssetRegister):
    client = await get_arango_client()
    if not client:
        return ArangoResponse(success=False, error="ArangoDB not available")
    res = await client.register_asset(body.presentationId, body.category, body.name, body.url, path=body.path, size=body.size, mime=body.mime)
    return ArangoResponse(success=bool(res.get('ok')), data=res)

class TemplateSet(BaseModel):
    name: str

@router.post("/presentations/{presentation_id}/template", response_model=ArangoResponse)
async def set_template(presentation_id: str, body: TemplateSet):
    client = await get_arango_client()
    if not client:
        return ArangoResponse(success=False, error="ArangoDB not available")
    tmpl = await client.create_project_node(presentation_id, 'template', { 'name': body.name })
    try:
        await client.create_project_edge(presentation_id, 'has_template', f'presentations/{presentation_id}', (tmpl.get('node') or {}).get('_id'))
    except Exception:
        pass
    return ArangoResponse(success=True, data=tmpl)

class SlideUseAsset(BaseModel):
    url: str



class GraphResponse(BaseModel):
    slides: list[dict[str, Any]] = Field(default_factory=list)
    assets: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)

@router.post("/presentations/{presentation_id}/slides/{slide_index}/use-asset", response_model=ArangoResponse)
async def slide_use_asset(presentation_id: str, slide_index: int, body: SlideUseAsset):
    client = await get_arango_client()
    if not client:
        return ArangoResponse(success=False, error="ArangoDB not available")
    db = client._db  # type: ignore
    # Resolve asset
    cursor = db.aql.execute('FOR a IN assets FILTER a.presentation_id == @pid AND a.url == @url LIMIT 1 RETURN a', bind_vars={'pid': presentation_id, 'url': body.url})
    arr = list(cursor)
    if not arr:
        return ArangoResponse(success=False, error="Asset not found")
    asset = arr[0]
    # Resolve latest slide
    cursor = db.aql.execute('FOR s IN slides FILTER s.presentation_id == @pid AND s.slide_index == @idx SORT s.version DESC LIMIT 1 RETURN s', bind_vars={'pid': presentation_id, 'idx': int(slide_index)})
    sarr = list(cursor)
    if not sarr:
        return ArangoResponse(success=False, error="Slide not found")
    slide = sarr[0]
    # Insert content edge
    if not db.has_collection('content_edges'):
        db.create_collection('content_edges', edge=True)
    db.collection('content_edges').insert({
        '_from': slide.get('_id') or f"slides/{slide.get('_key')}",
        '_to': asset.get('_id') or f"assets/{asset.get('_key')}",
        'presentation_id': presentation_id,
        'relation': 'slide_uses_asset',
        'created_at': datetime.now().isoformat(),
    })
    return ArangoResponse(success=True, data={'from': slide.get('_id'), 'to': asset.get('_id')})

@router.get("/presentations/{presentation_id}/graph", response_model=ArangoResponse)
async def get_presentation_graph(presentation_id: str) -> ArangoResponse:
    client = await get_arango_client()
    if not client:
        return ArangoResponse(success=False, error="ArangoDB not available")
    try:
        slides = await client.get_latest_slides(presentation_id) or []
    except Exception:
        slides = []
    db = client._db  # type: ignore
    assets = []
    try:
        cursor = db.aql.execute('FOR a IN assets FILTER a.presentation_id == @pid RETURN { id: a._id, key: a._key, name: a.name, url: a.url, kind: a.category || a.kind }', bind_vars={'pid': presentation_id})
        assets = list(cursor)
    except Exception:
        pass
    edges = []
    try:
        if db.has_collection('content_edges'):
            cursor = db.aql.execute('FOR e IN content_edges FILTER e.presentation_id == @pid RETURN e', bind_vars={'pid': presentation_id})
            edges = list(cursor)
    except Exception:
        pass
    return ArangoResponse(success=True, data={'slides': slides, 'assets': assets, 'edges': edges})
