"""
ArangoDB API routes for presentation persistence.

This module provides REST endpoints that interface with the existing
EnhancedArangoClient to handle presentation data storage and retrieval.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
import asyncio
from datetime import datetime
import os

# Import the existing ArangoDB client
try:
    from agents.base_arango_client import EnhancedArangoClient
    ARANGO_AVAILABLE = True
except ImportError:
    ARANGO_AVAILABLE = False
    logging.warning("ArangoDB client not available - endpoints will return mock responses")

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/v1/arango", tags=["presentations", "arango"])

# Pydantic models for request/response
class CreatePresentationRequest(BaseModel):
    presentation_id: str = Field(..., description="Unique presentation identifier")
    user_id: str = Field(default="default", description="User identifier")
    status: str = Field(default="initial", description="Initial presentation status")

class UpdateStatusRequest(BaseModel):
    status: str = Field(..., description="New presentation status")
    title: Optional[str] = Field(None, description="Optional presentation title")

class ClarificationData(BaseModel):
    sequence: int
    role: str  # "user" or "assistant"
    content: str

class BatchOperation(BaseModel):
    operation: str = Field(..., description="Operation type")
    data: Dict[str, Any] = Field(..., description="Operation data")

class BatchRequest(BaseModel):
    operations: List[BatchOperation] = Field(..., description="List of operations to execute")

class PresentationState(BaseModel):
    metadata: Optional[Dict] = None
    clarifications: Optional[List[Dict]] = None
    outline: Optional[Dict] = None
    slides: Optional[List[Dict]] = None

class ArangoResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None

# Global ArangoDB client instance
arango_client: Optional[EnhancedArangoClient] = None

async def get_arango_client():
    """Get or create ArangoDB client instance"""
    global arango_client

    if not ARANGO_AVAILABLE:
        return None

    if arango_client is None:
        arango_client = EnhancedArangoClient(agent_name="presentation_api")
        try:
            await arango_client.connect()
            logger.info("ArangoDB client connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            arango_client = None

    return arango_client

@router.post("/presentations", response_model=ArangoResponse)
async def create_presentation(request: CreatePresentationRequest):
    """Create a new presentation in ArangoDB"""
    try:
        client = await get_arango_client()
        if not client:
            return ArangoResponse(
                success=False,
                error="ArangoDB not available",
                message="Using localStorage fallback"
            )

        result = await client.create_presentation(
            presentation_id=request.presentation_id,
            user_id=request.user_id
        )

        return ArangoResponse(
            success=True,
            data=result,
            message="Presentation created successfully"
        )

    except Exception as e:
        logger.error(f"Failed to create presentation: {e}")
        return ArangoResponse(
            success=False,
            error=str(e)
        )

@router.get("/presentations", response_model=ArangoResponse)
async def list_presentations(limit: int = 50, offset: int = 0):
    """List presentations metadata"""
    try:
        client = await get_arango_client()
        if not client:
            return ArangoResponse(success=False, error="ArangoDB not available", message="Using localStorage fallback")
        items = await client.list_presentations(limit=limit, offset=offset)
        return ArangoResponse(success=True, data=items)
    except Exception as e:
        logger.error(f"Failed to list presentations: {e}")
        return ArangoResponse(success=False, error=str(e))

@router.put("/presentations/{presentation_id}/status", response_model=ArangoResponse)
async def update_presentation_status(presentation_id: str, request: UpdateStatusRequest):
    """Update presentation status and metadata"""
    try:
        client = await get_arango_client()
        if not client:
            return ArangoResponse(
                success=False,
                error="ArangoDB not available",
                message="Using localStorage fallback"
            )

        result = await client.update_presentation_status(
            presentation_id=presentation_id,
            status=request.status,
            title=request.title
        )

        return ArangoResponse(
            success=True,
            data=result,
            message="Presentation status updated successfully"
        )

    except Exception as e:
        logger.error(f"Failed to update presentation status: {e}")
        return ArangoResponse(
            success=False,
            error=str(e)
        )

@router.get("/presentations/{presentation_id}/state", response_model=ArangoResponse)
async def get_presentation_state(presentation_id: str):
    """Get complete presentation state from all collections"""
    try:
        client = await get_arango_client()
        if not client:
            return ArangoResponse(
                success=False,
                error="ArangoDB not available",
                message="Using localStorage fallback"
            )

        result = await client.get_presentation_state(presentation_id)

        return ArangoResponse(
            success=True,
            data=result,
            message="Presentation state retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Failed to get presentation state: {e}")
        return ArangoResponse(
            success=False,
            error=str(e)
        )

@router.post("/presentations/batch", response_model=ArangoResponse)
async def batch_operations(request: BatchRequest):
    """Execute multiple operations in batch"""
    try:
        client = await get_arango_client()
        if not client:
            return ArangoResponse(
                success=False,
                error="ArangoDB not available",
                message="Using localStorage fallback"
            )

        results = []

        for operation in request.operations:
            try:
                if operation.operation == "update_metadata":
                    data = operation.data
                    await client.create_presentation(
                        presentation_id=data["presentation_id"],
                        user_id=data.get("user_id", "default")
                    )
                    if "title" in data or "status" in data:
                        result = await client.update_presentation_status(
                            presentation_id=data["presentation_id"],
                            status=data.get("status", "initial"),
                            title=data.get("title")
                        )
                        results.append({"operation": "update_metadata", "result": result})

                elif operation.operation == "save_clarifications":
                    data = operation.data
                    clarifications = data.get("clarifications") or []
                    await client.replace_clarifications(
                        presentation_id=data["presentation_id"],
                        clarifications=clarifications
                    )
                    results.append({"operation": "save_clarifications", "count": len(clarifications)})

                elif operation.operation == "save_outline":
                    data = operation.data
                    result = await client.save_outline(
                        presentation_id=data["presentation_id"],
                        outline=data["outline"]
                    )
                    results.append({"operation": "save_outline", "result": result})

                elif operation.operation == "save_slides":
                    data = operation.data
                    from agents.base_arango_client import SlideContent
                    slides_payload = []
                    for raw in data.get("slides", []):
                        idx = raw.get("slide_index")
                        slide_content = SlideContent(
                            presentation_id=data["presentation_id"],
                            slide_index=int(idx) if idx is not None else len(slides_payload),
                            title=raw.get("title") or '',
                            content=raw.get("content") or [],
                            speaker_notes=raw.get("speaker_notes") or '',
                            image_prompt=raw.get("image_prompt") or '',
                            image_url=raw.get("image_url"),
                            use_generated_image=raw.get("use_generated_image"),
                            asset_image_url=raw.get("asset_image_url"),
                            design_code=raw.get("design_code"),
                            design_spec=raw.get("design_spec"),
                            constraints_override=raw.get("constraints_override"),
                            use_constraints=raw.get("use_constraints"),
                        )
                        slides_payload.append(slide_content)
                    result = await client.replace_slides(data["presentation_id"], slides_payload)
                    results.append({"operation": "save_slides", "count": result.get('count', len(slides_payload))})

                elif operation.operation == "save_review":
                    data = operation.data
                    result = await client.save_review(
                        presentation_id=data["presentation_id"],
                        slide_index=int(data["slide_index"]),
                        review_data=data.get("review_data", {})
                    )
                    results.append({"operation": "save_review", "result": result})

                elif operation.operation == "save_goals":
                    data = operation.data
                    goals_text = data.get('clarified_goals', '')
                    await client.upsert_presentation_metadata(
                        presentation_id=data["presentation_id"],
                        patch={'clarified_goals': goals_text}
                    )
                    results.append({"operation": "save_goals", "result": {'ok': True, 'clarified_goals': goals_text}})

                elif operation.operation == "save_script":
                    data = operation.data
                    await client.save_script(
                        presentation_id=data["presentation_id"],
                        script_content=data.get('script') or data.get('script_content') or ''
                    )
                    results.append({"operation": "save_script", "result": {'ok': True}})

                else:
                    logger.warning(f"Unknown operation: {operation.operation}")
                    results.append({"operation": operation.operation, "error": "Unknown operation"})

            except Exception as e:
                logger.error(f"Batch operation {operation.operation} failed: {e}")
                results.append({"operation": operation.operation, "error": str(e)})

        return ArangoResponse(
            success=True,
            data={"results": results},
            message=f"Executed {len(request.operations)} batch operations"
        )

    except Exception as e:
        logger.error(f"Batch operations failed: {e}")
        return ArangoResponse(
            success=False,
            error=str(e)
        )

@router.get("/health", response_model=ArangoResponse)
async def arango_health_check():
    """Check ArangoDB connection health"""
    try:
        client = await get_arango_client()
        if not client:
            return ArangoResponse(
                success=False,
                error="ArangoDB not available",
                data={
                    "status": "unavailable",
                    "timestamp": datetime.now().isoformat(),
                    "message": "Using localStorage fallback"
                }
            )

        health_result = await client.health_check()

        return ArangoResponse(
            success=health_result["healthy"],
            data=health_result,
            message="ArangoDB health check completed"
        )

    except Exception as e:
        logger.error(f"ArangoDB health check failed: {e}")
        return ArangoResponse(
            success=False,
            error=str(e),
            data={
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
        )

# Messages listing
@router.get("/presentations/{presentation_id}/messages", response_model=ArangoResponse)
async def list_messages(presentation_id: str, agent: Optional[str] = None, limit: int = 50, offset: int = 0):
    try:
        client = await get_arango_client()
        if not client:
            return ArangoResponse(success=False, error="ArangoDB not available")
        rows = await client.list_messages(presentation_id, agent=agent, limit=limit, offset=offset)
        return ArangoResponse(success=True, data=rows)
    except Exception as e:
        logger.error(f"Failed to list messages: {e}")
        return ArangoResponse(success=False, error=str(e))

# Cleanup function for application shutdown
async def cleanup_arango_client():
    """Clean up ArangoDB client connection"""
    global arango_client
    if arango_client:
        try:
            await arango_client.close()
            logger.info("ArangoDB client connection closed")
        except Exception as e:
            logger.error(f"Error closing ArangoDB client: {e}")
        finally:
            arango_client = None

# Reviews listing
@router.get("/presentations/{presentation_id}/slides/{slide_index}/reviews", response_model=ArangoResponse)
async def list_reviews(presentation_id: str, slide_index: int, limit: int = 10, offset: int = 0):
    try:
        client = await get_arango_client()
        if not client:
            return ArangoResponse(success=False, error="ArangoDB not available")
        rows = await client.get_reviews(presentation_id, slide_index, limit, offset)
        # Normalize response: only return review_data + timestamps
        data = [
            {
                'created_at': r.get('created_at'),
                'agent_source': r.get('agent_source'),
                'review_data': r.get('review_data') or {},
            }
            for r in rows
        ]
        return ArangoResponse(success=True, data=data)
    except Exception as e:
        logger.error(f"Failed to list reviews: {e}")
        return ArangoResponse(success=False, error=str(e))

# --- Project initialization ---
class InitProjectRequest(BaseModel):
    initialInput: Dict[str, Any]

@router.post("/presentations/{presentation_id}/init", response_model=ArangoResponse)
async def init_project(presentation_id: str, body: InitProjectRequest):
    try:
        client = await get_arango_client()
        if not client:
            return ArangoResponse(success=False, error="ArangoDB not available")

        # Ensure local folders exist
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'public', 'uploads', presentation_id))
        folders = {
            'base': base_dir,
            'content': os.path.join(base_dir, 'content'),
            'style': os.path.join(base_dir, 'style'),
            'graphics': os.path.join(base_dir, 'graphics'),
        }
        for p in folders.values():
            try:
                os.makedirs(p, exist_ok=True)
            except Exception:
                pass

        # Upsert presentation metadata with folder links
        await client.upsert_presentation_metadata(presentation_id, {
            'folders': {
                'baseUrl': f"/uploads/{presentation_id}/",
                'contentUrl': f"/uploads/{presentation_id}/content/",
                'styleUrl': f"/uploads/{presentation_id}/style/",
                'graphicsUrl': f"/uploads/{presentation_id}/graphics/",
            },
            'preferences': body.initialInput,
        })

        # Create nodes
        cfg = await client.create_project_node(presentation_id, 'config', body.initialInput)
        content_node = await client.create_project_node(presentation_id, 'content', { 'folderUrl': f"/uploads/{presentation_id}/content/" })
        style_node = await client.create_project_node(presentation_id, 'style', { 'folderUrl': f"/uploads/{presentation_id}/style/" })
        graphics_node = await client.create_project_node(presentation_id, 'graphics', { 'folderUrl': f"/uploads/{presentation_id}/graphics/" })

        def unwrap(n):
            return (n or {}).get('node', {})
        await client.create_project_link(presentation_id, 'has_config', { '_id': f'presentations/{presentation_id}' }, unwrap(cfg))
        await client.create_project_link(presentation_id, 'has_content', { '_id': f'presentations/{presentation_id}' }, unwrap(content_node))
        await client.create_project_link(presentation_id, 'has_style', { '_id': f'presentations/{presentation_id}' }, unwrap(style_node))
        await client.create_project_link(presentation_id, 'has_graphics', { '_id': f'presentations/{presentation_id}' }, unwrap(graphics_node))

        return ArangoResponse(success=True, data={ 'folders': {
            'baseUrl': f"/uploads/{presentation_id}/",
            'contentUrl': f"/uploads/{presentation_id}/content/",
            'styleUrl': f"/uploads/{presentation_id}/style/",
            'graphicsUrl': f"/uploads/{presentation_id}/graphics/",
        } })
    except Exception as e:
        logger.error(f"init_project failed: {e}")
        return ArangoResponse(success=False, error=str(e))
