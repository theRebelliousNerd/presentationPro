"""
ADK/A2A Orchestrator - FastAPI Application with Dev UI

This module exposes the functionality of the ADK agents through a RESTful API,
allowing a web application to drive the presentation generation workflow.
Now includes ADK Dev UI for agent testing and development.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import asyncio
import httpx
import logging
import os
import uuid
from datetime import datetime

# Import agent wrapper classes and their data models
from agents.wrappers import (
    ClarifierAgent, ClarifierInput,
    OutlineAgent, OutlineInput,
    SlideWriterAgent, SlideWriterInput,
    CriticAgent, CriticInput,
    DesignAgent, DesignInput,
    NotesPolisherAgent, NotesPolisherInput,
    ScriptWriterAgent, ScriptWriterInput,
    ResearchAgent, ResearchInput
)

# Import ADK framework
import adk
from adk.dev_ui import get_dev_ui_server

# Import tools for direct use in utility endpoints
from tools import (
    ArangoGraphRAGTool,
    Asset, IngestResponse, RetrieveResponse,
    VisionContrastTool, VisionAnalyzeInput, VisionAnalyzeOutput
)
from tools.web_search_tool import set_global_cache_config, clear_global_cache
from app.design_sanitize import (
    validate_html, validate_css, validate_svg,
    sanitize_html, sanitize_css, sanitize_svg,
)

# Optional Arango persistence routes
try:
    from app import arango_routes
    _HAS_ARANGO_ROUTES = True
except Exception:
    arango_routes = None  # type: ignore
    _HAS_ARANGO_ROUTES = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI(
    title="ADK/A2A Orchestrator",
    version="1.0.0",
    description="An API for orchestrating a multi-agent system with ADK Dev UI support."
)

# Add CORS middleware for Dev UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Arango persistence API (robust)
if _HAS_ARANGO_ROUTES:
    try:
        app.include_router(arango_routes.router)  # type: ignore[attr-defined]
        logger.info("Arango routes included (flag)")
    except Exception as e:
        logger.warning(f"Failed to include Arango routes (flag): {e}")
else:
    # Second-chance attempt to import and mount even if the earlier import hook failed
    try:
        from app import arango_routes as _arango_routes  # type: ignore
        app.include_router(_arango_routes.router)
        logger.info("Arango routes included (late)")
    except Exception as e:
        logger.warning(f"Arango routes unavailable: {e}")
        # Provide minimal fallback endpoints to keep frontend workflow unblocked
        from fastapi import APIRouter
        fallback = APIRouter(prefix="/v1/arango", tags=["arango-fallback"])

        @fallback.post("/presentations")
        def _fallback_create():
            return {"success": False, "error": "ArangoDB not available", "message": "Using localStorage fallback"}

        @fallback.get("/presentations/{presentation_id}/state")
        def _fallback_state(presentation_id: str):
            return {"success": False, "error": "ArangoDB not available", "message": "Using localStorage fallback"}

        @fallback.post("/presentations/batch")
        def _fallback_batch():
            return {"success": False, "error": "ArangoDB not available", "message": "Using localStorage fallback"}

        @fallback.get("/health")
        def _fallback_health():
            return {"success": False, "data": {"status": "unavailable"}}

        app.include_router(fallback)
        logger.info("Arango fallback routes included")

# Include extra Arango routes (assets/register, template, slide use-asset)
try:
    from app import arango_extras  # type: ignore
    app.include_router(arango_extras.router)  # type: ignore[attr-defined]
    logger.info("Arango extras routes included")
except Exception as e:
    logger.warning(f"Failed to include Arango extras routes: {e}")

# Serve generated images
from fastapi.staticfiles import StaticFiles

# --- Agent Initialization ---
# Instantiate agents at the global scope to be reused across requests.
# This is more efficient than creating new instances for every API call.
clarifier_agent = ClarifierAgent()
outline_agent = OutlineAgent()
slide_writer_agent = SlideWriterAgent()
critic_agent = CriticAgent()
notes_polisher_agent = NotesPolisherAgent()
design_agent = DesignAgent()
script_writer_agent = ScriptWriterAgent()
research_agent = ResearchAgent()
vision_contrast_tool = VisionContrastTool()
generated_images_dir = os.path.join(os.path.dirname(__file__), 'generated_images')
exports_dir = os.path.join(os.path.dirname(__file__), 'exports')
try:
    os.makedirs(generated_images_dir, exist_ok=True)
    os.makedirs(exports_dir, exist_ok=True)
except Exception:
    pass
app.mount("/generated-images", StaticFiles(directory=generated_images_dir), name="generated_images")
app.mount("/exports", StaticFiles(directory=exports_dir), name="exports")
logger.info(f"Static mount '/generated-images' -> {generated_images_dir} (exists={os.path.isdir(generated_images_dir)})")

# Initialize Graph RAG tool (real Arango-backed)
try:
    graph_rag_tool = ArangoGraphRAGTool()
    logger.info("ArangoGraphRAGTool initialized")
except Exception as e:
    logger.warning(f"Failed to initialize ArangoGraphRAGTool, using no-op. Error: {e}")
    class _NoopRAG:
        def ingest(self, assets):
            return IngestResponse(ok=True, docs=0, chunks=0)
        def retrieve(self, presentation_id, query, limit=5):
            return RetrieveResponse(chunks=[])
    graph_rag_tool = _NoopRAG()

# --- Core Presentation Workflow Endpoints ---

@app.post("/v1/clarify")
async def clarify(data: ClarifierInput, request: Request):
    """Endpoint to run the ClarifierAgent."""
    # Enrich with asset context snippets if presentationId provided
    try:
        if data.presentationId:
            initial_text = (data.initialInput or {}).get('text') or ''
            query = initial_text if isinstance(initial_text, str) and initial_text.strip() else 'overview'
            retr = graph_rag_tool.retrieve(data.presentationId, query, limit=5)  # type: ignore[attr-defined]
            snippets = [getattr(c, 'text', None) or (c.get('text') if isinstance(c, dict) else '') for c in (getattr(retr, 'chunks', []) or [])]
            data.assetContext = [s.strip()[:500] for s in snippets if isinstance(s, str) and s.strip()]
    except Exception as e:
        logger.warning(f"Clarify context enrichment failed: {e}")
    # Basic inbound logging
    try:
        pid = getattr(data, 'presentationId', None)
        if not pid:
            try:
                body = await request.json()
                pid = body.get('presentationId')
            except Exception:
                pid = None
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="clarifier")
            await client.connect()
            initial_text = (data.initialInput or {}).get('text') if isinstance(data.initialInput, dict) else None
            await client.save_message(pid, 'clarifier', 'user', initial_text or '[no text]', 'llm', {'endpoint':'/v1/clarify'})
            await client.close()
    except Exception:
        pass
    result = clarifier_agent.run(data)
    # Basic outbound logging
    try:
        pid = getattr(data, 'presentationId', None)
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="clarifier")
            await client.connect()
            refined = result.data.get('refinedGoals') if isinstance(result.data, dict) else None
            await client.save_message(pid, 'clarifier', 'assistant', refined or '[ok]', 'llm', {'endpoint':'/v1/clarify'})
            await client.close()
    except Exception:
        pass
    # Return the refined goals and finished status as expected by frontend
    return {
        "refinedGoals": result.data.get('response', ''),  # Changed from 'refinedGoals' to 'response'
        "finished": result.data.get('finished', False),
        "initialInputPatch": result.data.get('initialInputPatch'),
        "usage": result.usage.model_dump()
    }

@app.post("/v1/outline")
async def outline(data: OutlineInput, request: Request):
    """Endpoint to run the OutlineAgent."""
    # Inbound logging
    try:
        pid = getattr(data, 'presentationId', None)
        if not pid:
            try:
                body = await request.json()
                pid = body.get('presentationId')
            except Exception:
                pid = None
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="outline")
            await client.connect()
            await client.save_message(pid, 'outline', 'user', (data.clarifiedContent or '') if hasattr(data,'clarifiedContent') else '', 'llm', {'endpoint':'/v1/outline'})
            await client.close()
    except Exception:
        pass
    result = outline_agent.run(data)
    try:
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="outline")
            await client.connect()
            out = result.data.get('outline') if isinstance(result.data, dict) else None
            await client.save_message(pid, 'outline', 'assistant', "\n".join(out or []), 'llm', {'endpoint':'/v1/outline'})
            await client.close()
    except Exception:
        pass
    return {"outline": result.data['outline'], "usage": result.usage.model_dump()}

@app.post("/v1/slide/write")
async def write_slide(data: SlideWriterInput, request: Request):
    """Endpoint to run the SlideWriterAgent."""
    try:
        pid = getattr(data, 'presentationId', None)
        if not pid:
            try:
                body = await request.json()
                pid = body.get('presentationId')
            except Exception:
                pid = None
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="slide_writer")
            await client.connect()
            await client.save_message(pid, 'slide_writer', 'user', f"outline count: {len(getattr(data,'outline',[]) or [])}", 'llm', {'endpoint':'/v1/slide/write'})
            await client.close()
    except Exception:
        pass
    result = slide_writer_agent.run(data)
    try:
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="slide_writer")
            await client.connect()
            titles = '; '.join([ (s.get('title') or '') for s in (result.data or []) ][:3])
            snippet = titles or '[no slides returned]'
            await client.save_message(pid, 'slide_writer', 'assistant', snippet, 'llm', {'endpoint':'/v1/slide/write'})
            await client.close()
    except Exception:
        pass
    # result.data is already a list of slides
    return {"slides": result.data, "usage": result.usage.model_dump()}

@app.post("/v1/slide/critique")
async def critique_slide(data: CriticInput, request: Request):
    """Endpoint to run the CriticAgent, with optional Arango review persistence."""
    # Inbound log
    try:
        pid = getattr(data, 'presentationId', None)
        if not pid:
            try:
                body = await request.json()
                pid = body.get('presentationId')
            except Exception:
                pid = None
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="critic")
            await client.connect()
            msg = f"title: {data.slide.get('title','')}, bullets: {len(data.slide.get('content',[]))}"
            await client.save_message(pid, 'critic', 'user', msg, 'llm', {'endpoint':'/v1/slide/critique'})
            await client.close()
    except Exception:
        pass
    result = critic_agent.run(data)
    payload = result.data
    slide_out: Dict[str, Any]
    review: Optional[Dict[str, Any]] = None
    if isinstance(payload, dict) and "slide" in payload:
        slide_out = payload.get("slide") or {}
        review = payload.get("review")
    else:
        slide_out = payload

    # Augment review only if explicitly enabled by env flag
    try:
        if os.environ.get('VISIONCV_AUTO_QA', 'false').lower() == 'true':
            body = await request.json()
            screenshot = None
            try:
                screenshot = (body.get('slide') or {}).get('screenshotDataUrl')
            except Exception:
                screenshot = None
            if screenshot and (os.environ.get('VISIONCV_URL') or os.environ.get('ADK_BASE_URL')):
                issues = []
                suggestions = []
                # Blur check
                try:
                    blur = await _visioncv_call_http('/v1/visioncv/blur', { 'screenshotDataUrl': screenshot })
                    if isinstance(blur, dict) and float(blur.get('blur_score', 9999)) < 800.0:
                        issues.append('Image appears blurry (low Laplacian variance).')
                        suggestions.append('Replace with a sharper image or reduce its size.')
                except Exception:
                    pass
                # Contrast check
                try:
                    contrast = await _visioncv_call_http('/v1/vision/analyze', { 'screenshotDataUrl': screenshot })
                    if isinstance(contrast, dict) and bool(contrast.get('recommendDarken')):
                        issues.append('Low text/background contrast detected.')
                        suggestions.append('Apply a dark overlay or choose a higher-contrast background.')
                except Exception:
                    pass
                if issues or suggestions:
                    if review is None:
                        review = { 'issues': [], 'suggestions': [] }
                    review['issues'] = (review.get('issues') or []) + issues
                    review['suggestions'] = (review.get('suggestions') or []) + suggestions
    except Exception:
        pass

    # Persist review if available and identifiers provided
    if review and data.presentationId is not None and data.slideIndex is not None:
        try:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="critic")
            await client.connect()
            await client.save_review(data.presentationId, int(data.slideIndex), review)
            await client.close()
        except Exception as e:
            logger.warning(f"Failed to persist critic review: {e}")

    # Outbound log
    try:
        pid = getattr(data, 'presentationId', None)
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="critic")
            await client.connect()
            out_msg = f"updated: {slide_out.get('title','')}"
            await client.save_message(pid, 'critic', 'assistant', out_msg, 'llm', {'endpoint':'/v1/slide/critique'})
            await client.close()
    except Exception:
        pass
    return {"slide": slide_out, "review": review, "usage": result.usage.model_dump()}


VISION_TOOL_MAP: Dict[str, str] = {
    '/v1/visioncv/blur': 'critic.assess_blur',
    '/v1/vision/analyze': 'critic.color_contrast',
}

async def _visioncv_call_http(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    vision_url = os.environ.get('VISIONCV_URL')
    tool_name = VISION_TOOL_MAP.get(path)
    if vision_url and tool_name:
        try:
            from shared.visioncv_client import call_tool as _vc_call
            args = dict(payload)
            result = await asyncio.to_thread(_vc_call, tool_name, args)
            if isinstance(result, dict):
                return result
        except Exception as exc:
            logger.warning(f"VisionCV MCP call failed for {tool_name}: {exc}")
    base = os.environ.get('ADK_BASE_URL')
    if base:
        base_url = base.rstrip('/')
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{base_url}{path}", json=payload)
            r.raise_for_status()
            return r.json()
    async with httpx.AsyncClient(app=app, base_url='http://vision-proxy.local', timeout=10.0) as client:
        r = await client.post(path, json=payload)
        r.raise_for_status()
        return r.json()

@app.post("/v1/slide/polish_notes")
async def polish_notes(data: NotesPolisherInput, request: Request):
    """Endpoint to run the NotesPolisherAgent."""
    try:
        pid = getattr(data, 'presentationId', None)
        if not pid:
            try:
                body = await request.json()
                pid = body.get('presentationId')
            except Exception:
                pid = None
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="notes_polisher")
            await client.connect()
            await client.save_message(pid, 'notes_polisher', 'user', (data.speakerNotes or '') if hasattr(data,'speakerNotes') else '', 'llm', {'endpoint':'/v1/slide/polish_notes'})
            await client.close()
    except Exception:
        pass
    result = notes_polisher_agent.run(data)
    try:
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="notes_polisher")
            await client.connect()
            preview = (result.data.get('rephrasedSpeakerNotes') or '')[:280]
            await client.save_message(pid, 'notes_polisher', 'assistant', preview, 'llm', {'endpoint':'/v1/slide/polish_notes'})
            await client.close()
    except Exception:
        pass
    return {"rephrasedSpeakerNotes": result.data['rephrasedSpeakerNotes'], "usage": result.usage.model_dump()}

@app.post("/v1/slide/design")
async def design_slide(data: DesignInput, request: Request):
    """Endpoint to run the DesignAgent."""
    # Inbound log
    try:
        pid = getattr(data, 'presentationId', None)
        if not pid:
            try:
                body = await request.json()
                pid = body.get('presentationId')
            except Exception:
                pid = None
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="design")
            await client.connect()
            msg = f"slide: {(data.slide or {}).get('title','')}, pattern: {getattr(data,'pattern',None)}"
            await client.save_message(pid, 'design', 'user', msg, 'llm', {'endpoint':'/v1/slide/design'})
            await client.close()
    except Exception:
        pass
    result = design_agent.run(data)
    design_data = result.data
    # Backward compatible response; include new fields when present
    out = {
        "type": design_data.get('type', 'prompt'),
        "prompt": design_data.get('prompt'),
        "code": design_data.get('code'),
        "usage": result.usage.model_dump()
    }
    if isinstance(design_data, dict) and design_data.get('designSpec'):
        out["designSpec"] = design_data.get('designSpec')
    if isinstance(design_data, dict) and design_data.get('variants'):
        out["variants"] = design_data.get('variants')
    # Outbound log
    try:
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="design")
            await client.connect()
            await client.save_message(pid, 'design', 'assistant', out.get('type','code'), 'llm', {'endpoint':'/v1/slide/design'})
            await client.close()
    except Exception:
        pass
    return out

@app.post("/v1/script/generate")
async def generate_script(data: ScriptWriterInput, request: Request):
    """Endpoint to run the ScriptWriterAgent."""
    try:
        pid = getattr(data, 'presentationId', None)
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="script_writer")
            await client.connect()
            await client.save_message(pid, 'script_writer', 'user', f"slides: {len(getattr(data,'slides',[]) or [])}", 'llm', {'endpoint':'/v1/script/generate'})
            await client.close()
    except Exception:
        pass
    result = script_writer_agent.run(data)
    script = result.data.get('script', '')
    try:
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="script_writer")
            await client.connect()
            await client.save_message(pid, 'script_writer', 'assistant', (script or '')[:280], 'llm', {'endpoint':'/v1/script/generate'})
            await client.close()
    except Exception:
        pass
    return {"script": script, "usage": result.usage.model_dump()}


# --- Tool and Utility Endpoints ---

@app.post("/v1/research/backgrounds")
async def research_backgrounds(data: ResearchInput, request: Request):
    """Endpoint to run the ResearchAgent for background research."""
    try:
        pid = getattr(data, 'presentationId', None)
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="research")
            await client.connect()
            await client.save_message(pid, 'research', 'user', getattr(data,'query','') or '', 'llm', {'endpoint':'/v1/research/backgrounds'})
            await client.close()
    except Exception:
        pass
    result = research_agent.run(data)
    out = {"rules": result.data['rules'], "usage": result.usage.model_dump()}
    try:
        if isinstance(result.data, dict) and result.data.get('extractions'):
            out['extractions'] = result.data.get('extractions')
    except Exception:
        pass
    try:
        if pid:
            from agents.base_arango_client import EnhancedArangoClient
            client = EnhancedArangoClient(agent_name="research")
            await client.connect()
            preview = '\n'.join((out.get('rules') or [])[:5])
            await client.save_message(pid, 'research', 'assistant', preview or '[no rules]', 'llm', {'endpoint':'/v1/research/backgrounds'})
            try:
                existing = await client.get_research_notes(pid)
                new_note = {
                    'note_id': f"note-{uuid.uuid4().hex[:8]}",
                    'query': data.query or '',
                    'rules': out.get('rules') or [],
                    'allow_domains': data.allowDomains,
                    'top_k': data.topK,
                    'model': data.textModel,
                    'created_at': datetime.utcnow().isoformat(),
                    'extractions': out.get('extractions'),
                }
                already = False
                for row in existing:
                    try:
                        if (row.get('query') or '') == new_note['query'] and (row.get('rules') or []) == new_note['rules']:
                            already = True
                            break
                    except Exception:
                        continue
                if not already:
                    payload = []
                    for row in existing:
                        payload.append({
                            'note_id': row.get('note_id') or row.get('_key'),
                            'query': row.get('query'),
                            'rules': row.get('rules') or [],
                            'allow_domains': row.get('allow_domains') or [],
                            'top_k': row.get('top_k'),
                            'model': row.get('model'),
                            'created_at': row.get('created_at'),
                            'extractions': row.get('extractions'),
                        })
                    payload.append(new_note)
                    await client.replace_research_notes(pid, payload)
            except Exception as store_err:
                logger.warning(f"Failed to persist research note for {pid}: {store_err}")
            await client.close()
    except Exception:
        pass
    return out

@app.post("/v1/vision/analyze", response_model=VisionAnalyzeOutput)
def vision_analyze(data: VisionAnalyzeInput):
    """Endpoint to run contrast analysis. Uses VisionCV if configured, fallback to local tool."""
    try:
        from shared.visioncv_client import call_tool as _vc_call
        url = os.environ.get("VISIONCV_URL")
        if url:
            res = _vc_call("critic.color_contrast", {"screenshotDataUrl": data.screenshotDataUrl})
            return VisionAnalyzeOutput(**res)
    except Exception:
        pass
    return vision_contrast_tool.analyze(data)

# Optional VisionCV proxy endpoints
@app.post("/v1/visioncv/blur")
def visioncv_blur(data: VisionAnalyzeInput):
    try:
        from shared.visioncv_client import call_tool as _vc_call
        return _vc_call("critic.assess_blur", {"screenshotDataUrl": data.screenshotDataUrl})
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/visioncv/saliency")
def visioncv_saliency(data: VisionAnalyzeInput):
    try:
        from shared.visioncv_client import call_tool as _vc_call
        return _vc_call("design.saliency_spectral", {"screenshotDataUrl": data.screenshotDataUrl, "output_size": [96, 54]})
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/visioncv/empty_regions")
def visioncv_empty_regions(data: VisionAnalyzeInput):
    try:
        from shared.visioncv_client import call_tool as _vc_call
        return _vc_call("design.find_empty_regions", {"screenshotDataUrl": data.screenshotDataUrl})
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/visioncv/placement")
def visioncv_placement(data: VisionAnalyzeInput):
    try:
        from shared.visioncv_client import call_tool as _vc_call
        return _vc_call("design.suggest_placement", {"screenshotDataUrl": data.screenshotDataUrl})
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/visioncv/ocr")
def visioncv_ocr(data: Dict[str, str]):
    try:
        from shared.visioncv_client import call_tool as _vc_call
        return _vc_call("research.ocr_extract", {"imageDataUrl": data.get("imageDataUrl"), "lang": data.get("lang")})
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/visioncv/logo")
def visioncv_logo(data: Dict[str, str]):
    try:
        from shared.visioncv_client import call_tool as _vc_call
        return _vc_call("brand.detect_logo", {"target_image_b64": data.get("target_image_b64"), "reference_logo_b64": data.get("reference_logo_b64")})
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/visioncv/brand_colors")
def visioncv_brand_colors(data: Dict[str, Any]):
    try:
        from shared.visioncv_client import call_tool as _vc_call
        return _vc_call("brand.validate_brand_colors", {"imageDataUrl": data.get("imageDataUrl"), "brandPalette": data.get("brandPalette"), "tolerance": data.get("tolerance")})
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/visioncv/palette")
def visioncv_palette(data: Dict[str, Any]):
    try:
        from shared.visioncv_client import call_tool as _vc_call
        return _vc_call("design.extract_palette", {
            "imageDataUrl": data.get("imageDataUrl") or data.get("screenshotDataUrl"),
            "colors": data.get("colors"),
        })
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/visioncv/procedural_texture")
def visioncv_procedural_texture(data: Dict[str, Any]):
    try:
        from shared.visioncv_client import call_tool as _vc_call
        return _vc_call("design.generate_procedural_texture", {
            "width": data.get("width"),
            "height": data.get("height"),
            "texture_type": data.get("texture_type"),
            "parameters": data.get("parameters"),
        })
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/visioncv/noise")
def visioncv_noise(data: Dict[str, Any]):
    try:
        from shared.visioncv_client import call_tool as _vc_call
        return _vc_call("critic.measure_noise", {
            "screenshotDataUrl": data.get("screenshotDataUrl"),
            "imageDataUrl": data.get("imageDataUrl"),
        })
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/visioncv/contrast_ratio")
def visioncv_contrast_ratio(data: Dict[str, Any]):
    try:
        from shared.visioncv_client import call_tool as _vc_call
        return _vc_call("critic.check_color_contrast_ratio", {
            "fg": data.get("fg"),
            "bg": data.get("bg"),
            "level": data.get("level"),
            "fontSizePx": data.get("fontSizePx"),
        })
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/visioncv/bar_chart")
def visioncv_bar_chart(data: Dict[str, str]):
    try:
        from shared.visioncv_client import call_tool as _vc_call
        return _vc_call("research.extract_data_from_bar_chart", {"imageDataUrl": data.get("imageDataUrl")})
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/visioncv/line_graph")
def visioncv_line_graph(data: Dict[str, str]):
    try:
        from shared.visioncv_client import call_tool as _vc_call
        return _vc_call("research.extract_data_from_line_graph", {"imageDataUrl": data.get("imageDataUrl")})
    except Exception as e:
        return {"error": str(e)}

@app.get("/v1/visioncv/tools")
def visioncv_tools():
    try:
        from shared.visioncv_client import list_tools as _vc_list
        return _vc_list()
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/visioncv/tools")
def visioncv_tools_post():
    try:
        from shared.visioncv_client import list_tools as _vc_list
        return _vc_list()
    except Exception as e:
        return {"error": str(e)}

class IngestRequest(BaseModel):
    assets: List[Asset]

@app.post("/v1/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest):
    """Endpoint for ingesting assets into the Graph RAG store."""
    return graph_rag_tool.ingest(req.assets)

class RetrieveRequest(BaseModel):
    presentationId: str
    query: str
    limit: int = 5

@app.post("/v1/retrieve", response_model=RetrieveResponse)
def retrieve(data: RetrieveRequest):
    """Endpoint for retrieving chunks from the Graph RAG store."""
    return graph_rag_tool.retrieve(data.presentationId, data.query, data.limit)


# --- Design Image Subagent ---
from agents.design_image_agent import DesignImageAgent, ImageGenerateInput, ImageEditInput, save_image_to_file
image_agent = DesignImageAgent()

class ImageGenerateResponse(BaseModel):
    imageUrl: str
    width: int
    height: int
    usage: Optional[dict] = None

@app.post("/v1/image/generate", response_model=ImageGenerateResponse)
def image_generate(req: ImageGenerateInput, request: Request):
    """Generate an overlay image (PNG) and return a public URL served by this app."""
    img = image_agent.generate_overlay(req)
    fpath = save_image_to_file(img, generated_images_dir)
    fname = os.path.basename(fpath)
    base = str(request.base_url).rstrip('/')
    url = f"{base}/generated-images/{fname}"
    return ImageGenerateResponse(imageUrl=url, width=img.width, height=img.height, usage={})

class ImageEditResponse(BaseModel):
    imageUrl: str
    width: int
    height: int
    usage: Optional[dict] = None

@app.post("/v1/image/edit", response_model=ImageEditResponse)
def image_edit(req: ImageEditInput, request: Request):
    """Edit a provided base image (data URL) and return a public URL."""
    edited = image_agent.edit_overlay(req)
    fpath = save_image_to_file(edited.convert("RGB"), generated_images_dir)
    fname = os.path.basename(fpath)
    base = str(request.base_url).rstrip('/')
    url = f"{base}/generated-images/{fname}"
    return ImageEditResponse(imageUrl=url, width=edited.width, height=edited.height, usage={})

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
uploads_dir = os.path.abspath(os.path.join(base_dir, 'public', 'uploads'))
try:
    os.makedirs(uploads_dir, exist_ok=True)
except Exception:
    pass
app.mount("/uploads", StaticFiles(directory=uploads_dir, check_dir=False), name="uploads")
logger.info(f"Static mount '/uploads' -> {uploads_dir} (exists={os.path.isdir(uploads_dir)})")

# --- Assets Catalog Endpoints ---
from tools.assets_catalog_tool import get_icon_svg, list_icon_candidates, get_pattern_svg, SvgResponse, IconInfo

class IconQuery(BaseModel):
    pack: str
    q: str = ""
    limit: int = 10

@app.post("/v1/assets/icons/list", response_model=list[IconInfo])
def assets_icons_list(query: IconQuery):
    return list_icon_candidates(query.pack, query.q, min(max(query.limit, 1), 50))

class IconGet(BaseModel):
    pack: str
    name: str

@app.post("/v1/assets/icons/get", response_model=SvgResponse)
def assets_icons_get(body: IconGet):
    svg = get_icon_svg(body.pack, body.name)
    if not svg:
        raise ValueError("Icon not found")
    return SvgResponse(svg=svg)

class PatternGet(BaseModel):
    name: str

@app.post("/v1/assets/patterns/get", response_model=SvgResponse)
def assets_patterns_get(body: PatternGet):
    svg = get_pattern_svg(body.name)
    if not svg:
        raise ValueError("Pattern not found")
    return SvgResponse(svg=svg)

# --- Image Save (from data URL) ---
class ImageSaveRequest(BaseModel):
    dataUrl: str

class ImageSaveResponse(BaseModel):
    imageUrl: str
    width: int | None = None
    height: int | None = None
    usage: dict | None = None

@app.post("/v1/image/save", response_model=ImageSaveResponse)
def image_save(req: ImageSaveRequest, request: Request):
    try:
        header, b64 = (req.dataUrl or '').split(',', 1)
    except Exception:
        b64 = req.dataUrl
    import base64, io
    from PIL import Image
    raw = base64.b64decode(b64)
    im = Image.open(io.BytesIO(raw))
    # Save under generated_images_dir
    os.makedirs(generated_images_dir, exist_ok=True)
    import uuid
    fname = f"{uuid.uuid4().hex}.png"
    fpath = os.path.join(generated_images_dir, fname)
    im.save(fpath, format='PNG', optimize=True)
    base = str(request.base_url).rstrip('/')
    url = f"{base}/generated-images/{fname}"
    return ImageSaveResponse(imageUrl=url, width=getattr(im, 'width', None), height=getattr(im, 'height', None), usage={})

# --- Export HTML ---
class ExportSlidesRequest(BaseModel):
    title: str | None = None
    slides: list[dict]

class ExportResponse(BaseModel):
    url: str

def _slide_to_html(slide: dict) -> str:
    # Basic conversion: prefer layout html/css + background; fallback to title + bullets
    ds = slide.get('designSpec') or {}
    bg_css = (((ds.get('background') or {}).get('css')) or '')
    bg_svg = (((ds.get('background') or {}).get('svg')) or '')
    layout = (ds.get('layout') or {})
    html = layout.get('html') or ''
    css = layout.get('css') or ''
    title = (slide.get('title') or '')
    bullets = slide.get('content') or []
    body = ''
    if html:
        # Use given HTML; drop slot population in export (assume already embedded)
        body = html
    else:
        items = ''.join([f'<li>{str(x)}</li>' for x in bullets])
        body = f'<section class="slide-default"><h1>{title}</h1><ul>{items}</ul></section>'
        css += (
            ".slide-default{position:relative;min-height:720px;display:flex;flex-direction:column;justify-content:center;padding:64px;color:#fff;}"
            ".slide-default h1{font:600 42px Montserrat, sans-serif;margin-bottom:16px;}"
            ".slide-default ul{padding-left:20px;line-height:1.3;font:400 20px Roboto, sans-serif;}"
        )
    bg_layer = f'<div class="bg" style="position:absolute;inset:0;background-image:{bg_css}"></div>' if bg_css else ''
    if bg_svg:
        bg_layer += f'<div class="bgsvg" style="position:absolute;inset:0">{bg_svg}</div>'
    style_block = f'<style>{css}</style>' if css else ''
    return f'<div class="slide" style="position:relative;min-height:720px">{bg_layer}<div class="content" style="position:relative;z-index:1">{body}</div>{style_block}</div>'

@app.post("/v1/export/html", response_model=ExportResponse)
def export_html(body: ExportSlidesRequest, request: Request):
    import uuid
    name = f"export_{uuid.uuid4().hex}.html"
    html_slides = '\n'.join([_slide_to_html(s) for s in (body.slides or [])])
    doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{(body.title or 'Presentation')}</title>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<style>html,body{margin:0;padding:0;background:#111}</style>"
        "</head><body>"
        f"{html_slides}"
        "</body></html>"
    )
    with open(os.path.join(exports_dir, name), 'w', encoding='utf-8') as f:
        f.write(doc)
    base = str(request.base_url).rstrip('/')
    return { 'url': f"{base}/exports/{name}" }

# --- Export PDF (simple) ---
class ExportPDFRequest(BaseModel):
    title: str | None = None
    slides: list[dict]

@app.post("/v1/export/pdf", response_model=ExportResponse)
def export_pdf(body: ExportPDFRequest, request: Request):
    # Simple PDF via reportlab (titles + bullets)
    try:
        from reportlab.lib.pagesizes import landscape
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        import uuid
        name = f"export_{uuid.uuid4().hex}.pdf"
        path = os.path.join(exports_dir, name)
        page_w, page_h = landscape((1280, 720))
        c = canvas.Canvas(path, pagesize=(page_w, page_h))
        for s in (body.slides or []):
            title = str(s.get('title') or '')
            bullets = s.get('content') or []
            # Background block (dark)
            c.setFillColorRGB(0.07, 0.07, 0.07)
            c.rect(0, 0, page_w, page_h, stroke=0, fill=1)
            # Title
            c.setFillColorRGB(1,1,1)
            c.setFont("Helvetica-Bold", 28)
            c.drawString(0.75*inch, page_h - 1.25*inch, title[:140])
            # Bullets
            c.setFont("Helvetica", 16)
            y = page_h - 1.8*inch
            for b in bullets[:10]:
                c.drawString(1.1*inch, y, f"• {str(b)[:160]}")
                y -= 0.45*inch
            c.showPage()
        c.save()
        base = str(request.base_url).rstrip('/')
        return { 'url': f"{base}/exports/{name}" }
    except Exception as e:
        # Fallback: write HTML and return URL
        return export_html(ExportSlidesRequest(title=body.title, slides=body.slides), request)

# --- Design validation/sanitization ---

class DesignCode(BaseModel):
    html: str | None = None
    css: str | None = None
    svg: str | None = None

@app.post("/v1/design/validate")
def design_validate(body: DesignCode):
    ok = True
    warnings: list[str] = []
    errors: list[str] = []
    if body.html:
        ok_h, w_h, e_h = validate_html(body.html)
        ok = ok and ok_h
        warnings += w_h
        errors += e_h
    if body.css:
        ok_c, w_c, e_c = validate_css(body.css)
        ok = ok and ok_c
        warnings += w_c
        errors += e_c
    if body.svg:
        ok_s, w_s, e_s = validate_svg(body.svg)
        ok = ok and ok_s
        warnings += w_s
        errors += e_s
    return { "ok": bool(ok), "warnings": warnings, "errors": errors }

@app.post("/v1/design/sanitize")
def design_sanitize(body: DesignCode):
    out: dict = {}
    warnings: list[str] = []
    if body.html:
        html, w = sanitize_html(body.html)
        out['html'] = html
        warnings += w
    if body.css:
        css, w = sanitize_css(body.css)
        out['css'] = css
        warnings += w
    if body.svg:
        svg, w = sanitize_svg(body.svg)
        out['svg'] = svg
        warnings += w
    out['warnings'] = warnings
    return out


# --- Cache Management Endpoints ---

class CacheConfig(BaseModel):
    enabled: Optional[bool] = None
    cacheTtl: Optional[int] = None  # Match frontend field name

@app.post("/v1/search/cache/config")
def search_cache_config(config: CacheConfig):
    """Configure the global web search cache."""
    return set_global_cache_config(enabled=config.enabled, ttl=config.cacheTtl)

class CacheClear(BaseModel):
    deleteFile: bool = True
    path: Optional[str] = None

@app.post("/v1/search/cache/clear")
def search_cache_clear(data: CacheClear):
    """Clear the global web search cache."""
    return clear_global_cache(delete_file=data.deleteFile, cache_path=data.path)


# --- Health Check ---

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"ok": True, "service": "adkpy", "version": "1.0.0", "dev_ui": True}


# --- Readiness Check ---

@app.get("/ready")
def ready():
    """Readiness endpoint that verifies static paths exist and are writable."""
    checks = {}
    ok = True
    for name, path in (
        ("generated_images", generated_images_dir),
        ("uploads", uploads_dir),
    ):
        exists = os.path.isdir(path)
        try:
            os.makedirs(path, exist_ok=True)
            writable = os.access(path, os.W_OK)
        except Exception:
            writable = False
        checks[name] = {"path": path, "exists": bool(exists), "writable": bool(writable)}
        ok = ok and bool(writable)
    return {"ok": ok, "paths": checks}


# --- ADK Dev UI Integration ---

# Initialize the Dev UI server with our FastAPI app
dev_ui = get_dev_ui_server()

# Register agents with ADK if using the v2 versions
try:
    # Try to import and register the ADK-enhanced agents
    from agents.clarifier_agent_v2 import ClarifierAgent as ClarifierAgentV2
    logger.info("ADK-enhanced ClarifierAgent registered")
except ImportError:
    logger.warning("ADK-enhanced agents not found, using standard versions")

# Log startup information
@app.on_event("startup")
async def startup_event():
    """Log startup information and agent registry."""
    from adk.agents import list_agents, get_agent
    # Ensure design rules are available
    try:
        from app.design_rules import ensure_design_rules
        ensure_design_rules()
        logger.info("Design rules ensured in ArangoDB")
    except Exception as e:
        logger.warning(f"Failed to ensure design rules: {e}")

    # Ensure graph schema available
    try:
        from app.graph_init import ensure_graph_schema
        ensure_graph_schema()
        logger.info("Graph schema ensured (collections + graphs)")
    except Exception as e:
        logger.warning(f"Graph schema setup failed: {e}")

    logger.info(f"ADK Orchestrator started")
    logger.info(f"API available at http://localhost:8088")

    # Log registered agents
    registered_agents = list_agents()
    if registered_agents:
        logger.info(f"Registered {len(registered_agents)} agents:")
        for agent_name in registered_agents:
            agent = get_agent(agent_name)
            if agent:
                logger.info(f"  - {agent.name}: {agent.description}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("ADK Orchestrator shutting down")
    # Attempt to clean up Arango client if router is mounted
    try:
        if _HAS_ARANGO_ROUTES and hasattr(arango_routes, "cleanup_arango_client"):
            await arango_routes.cleanup_arango_client()  # type: ignore[attr-defined]
    except Exception as e:
        logger.warning(f"Arango cleanup failed: {e}")

# --- Arango Extras (inline) ---
from pydantic import BaseModel

class AssetRegister(BaseModel):
    presentationId: str
    category: str
    name: str
    url: str
    path: str | None = None
    size: int | None = None
    mime: str | None = None

@app.post("/v1/arango/assets/register")
async def arango_assets_register(body: AssetRegister):
    try:
        from agents.base_arango_client import EnhancedArangoClient
        client = EnhancedArangoClient(agent_name="presentation_api")
        await client.connect()
        res = await client.register_asset(body.presentationId, body.category, body.name, body.url, path=body.path, size=body.size, mime=body.mime)
        await client.close()
        return { 'success': bool(res.get('ok')), 'data': res }
    except Exception as e:
        return { 'success': False, 'error': str(e) }

class TemplateSet(BaseModel):
    name: str

@app.post("/v1/arango/presentations/{presentation_id}/template")
async def arango_set_template(presentation_id: str, body: TemplateSet):
    try:
        from agents.base_arango_client import EnhancedArangoClient
        client = EnhancedArangoClient(agent_name="presentation_api")
        await client.connect()
        tmpl = await client.create_project_node(presentation_id, 'template', { 'name': body.name })
        try:
            await client.create_project_edge(presentation_id, 'has_template', f'presentations/{presentation_id}', (tmpl.get('node') or {}).get('_id'))
        except Exception:
            pass
        await client.close()
        return { 'success': True, 'data': tmpl }
    except Exception as e:
        return { 'success': False, 'error': str(e) }

class SlideUseAsset(BaseModel):
    url: str

@app.post("/v1/arango/presentations/{presentation_id}/slides/{slide_index}/use-asset")
async def arango_slide_use_asset(presentation_id: str, slide_index: int, body: SlideUseAsset):
    try:
        from agents.base_arango_client import EnhancedArangoClient
        client = EnhancedArangoClient(agent_name="presentation_api")
        await client.connect()
        db = client._db  # type: ignore
        cursor = db.aql.execute('FOR a IN assets FILTER a.presentation_id == @pid AND a.url == @url LIMIT 1 RETURN a', bind_vars={'pid': presentation_id, 'url': body.url})
        arr = list(cursor)
        if not arr:
            await client.close()
            return { 'success': False, 'error': 'Asset not found' }
        asset = arr[0]
        cursor = db.aql.execute('FOR s IN slides FILTER s.presentation_id == @pid AND s.slide_index == @idx SORT s.version DESC LIMIT 1 RETURN s', bind_vars={'pid': presentation_id, 'idx': int(slide_index)})
        sarr = list(cursor)
        if not sarr:
            await client.close()
            return { 'success': False, 'error': 'Slide not found' }
        slide = sarr[0]
        if not db.has_collection('content_edges'):
            db.create_collection('content_edges', edge=True)
        db.collection('content_edges').insert({
            '_from': slide.get('_id') or f"slides/{slide.get('_key')}",
            '_to': asset.get('_id') or f"assets/{asset.get('_key')}",
            'presentation_id': presentation_id,
            'relation': 'slide_uses_asset',
            'created_at': datetime.now().isoformat(),
        })
        await client.close()
        return { 'success': True, 'data': { 'from': slide.get('_id'), 'to': asset.get('_id') } }
    except Exception as e:
        return { 'success': False, 'error': str(e) }
