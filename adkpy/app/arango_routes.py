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
                    for clarification in data["clarifications"]:
                        result = await client.add_clarification(
                            presentation_id=data["presentation_id"],
                            role=clarification["role"],
                            content=clarification["content"]
                        )
                    results.append({"operation": "save_clarifications", "count": len(data["clarifications"])})

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
                    for slide in data["slides"]:
                        slide_content = SlideContent(
                            presentation_id=data["presentation_id"],
                            slide_index=slide["slide_index"],
                            title=slide["title"],
                            content=slide["content"],
                            speaker_notes=slide["speaker_notes"],
                            image_prompt=slide["image_prompt"]
                        )
                        result = await client.save_slide(slide_content)
                    results.append({"operation": "save_slides", "count": len(data["slides"])})

                elif operation.operation == "save_goals":
                    # Store clarified goals as a special clarification entry
                    data = operation.data
                    result = await client.add_clarification(
                        presentation_id=data["presentation_id"],
                        role="assistant",
                        content=f"CLARIFIED_GOALS: {data['clarified_goals']}"
                    )
                    results.append({"operation": "save_goals", "result": result})

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