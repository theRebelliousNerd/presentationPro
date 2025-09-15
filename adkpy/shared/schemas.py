"""
Shared Schemas

Common Pydantic models used across all agents.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, validator


# --- Base Request/Response Models ---

class BaseRequest(BaseModel):
    """Base request model with common fields."""
    trace_id: str = Field(description="Trace ID for request tracking")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    success: bool = Field(description="Whether the request was successful")
    trace_id: str = Field(description="Trace ID for request tracking")
    timestamp: float = Field(description="Response timestamp")
    duration_ms: Optional[int] = Field(None, description="Processing duration")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class ErrorResponse(BaseResponse):
    """Error response model."""
    success: bool = Field(default=False)
    error_code: str = Field(description="Error code")
    error_message: str = Field(description="Error message")
    error_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed error information"
    )


class SuccessResponse(BaseResponse):
    """Success response model."""
    success: bool = Field(default=True)
    data: Any = Field(description="Response data")


# --- Telemetry Models ---

class TelemetryData(BaseModel):
    """Telemetry data for tracking agent usage."""
    agent_name: str = Field(description="Agent name")
    operation: str = Field(description="Operation performed")
    model: Optional[str] = Field(None, description="Model used")
    prompt_tokens: int = Field(default=0, description="Prompt tokens used")
    completion_tokens: int = Field(default=0, description="Completion tokens")
    total_tokens: int = Field(default=0, description="Total tokens")
    duration_ms: int = Field(description="Operation duration in ms")
    cost: Optional[float] = Field(None, description="Estimated cost")
    timestamp: float = Field(description="Event timestamp")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional telemetry data"
    )

    @validator("total_tokens", always=True)
    def calculate_total_tokens(cls, v, values):
        """Calculate total tokens if not provided."""
        if v == 0:
            return values.get("prompt_tokens", 0) + values.get("completion_tokens", 0)
        return v


class MetricsData(BaseModel):
    """Metrics data for system monitoring."""
    metric_name: str = Field(description="Metric name")
    value: float = Field(description="Metric value")
    unit: Optional[str] = Field(None, description="Metric unit")
    tags: Dict[str, str] = Field(
        default_factory=dict,
        description="Metric tags"
    )
    timestamp: float = Field(description="Metric timestamp")


# --- Presentation Domain Models ---

class SlideType(str, Enum):
    """Types of slides."""
    TITLE = "title"
    CONTENT = "content"
    BULLET = "bullet"
    IMAGE = "image"
    CHART = "chart"
    COMPARISON = "comparison"
    CONCLUSION = "conclusion"


class DesignTheme(str, Enum):
    """Design themes."""
    BRAND = "brand"
    MUTED = "muted"
    DARK = "dark"
    LIGHT = "light"
    COLORFUL = "colorful"


class BackgroundPattern(str, Enum):
    """Background patterns."""
    GRADIENT = "gradient"
    SHAPES = "shapes"
    GRID = "grid"
    DOTS = "dots"
    WAVE = "wave"
    NONE = "none"


class SlideData(BaseModel):
    """Data for a single slide."""
    slide_number: int = Field(description="Slide number in sequence")
    title: str = Field(description="Slide title")
    content: List[str] = Field(
        default_factory=list,
        description="Slide content lines"
    )
    speaker_notes: Optional[str] = Field(
        None,
        description="Speaker notes for the slide"
    )
    slide_type: SlideType = Field(
        default=SlideType.CONTENT,
        description="Type of slide"
    )
    image_prompt: Optional[str] = Field(
        None,
        description="Prompt for image generation"
    )
    image_url: Optional[HttpUrl] = Field(
        None,
        description="URL of generated image"
    )
    background: Optional[Dict[str, Any]] = Field(
        None,
        description="Background design data"
    )
    citations: List[str] = Field(
        default_factory=list,
        description="Citations for the slide"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional slide metadata"
    )


class OutlineData(BaseModel):
    """Presentation outline data."""
    title: str = Field(description="Presentation title")
    sections: List[str] = Field(description="Main sections")
    subsections: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Subsections by section"
    )
    estimated_slides: int = Field(description="Estimated number of slides")
    duration_minutes: Optional[int] = Field(
        None,
        description="Estimated presentation duration"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional outline metadata"
    )


class PresentationRequest(BaseRequest):
    """Request for presentation generation."""
    topic: str = Field(description="Presentation topic")
    audience: Optional[str] = Field(
        None,
        description="Target audience"
    )
    goals: Optional[List[str]] = Field(
        None,
        description="Presentation goals"
    )
    constraints: Optional[Dict[str, Any]] = Field(
        None,
        description="Constraints (time, slides, etc.)"
    )
    style_preferences: Optional[Dict[str, Any]] = Field(
        None,
        description="Style preferences"
    )
    uploaded_files: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Uploaded file references"
    )
    design_theme: DesignTheme = Field(
        default=DesignTheme.BRAND,
        description="Design theme"
    )
    background_pattern: BackgroundPattern = Field(
        default=BackgroundPattern.GRADIENT,
        description="Background pattern"
    )


class PresentationResponse(BaseResponse):
    """Response for presentation generation."""
    presentation_id: str = Field(description="Generated presentation ID")
    title: str = Field(description="Presentation title")
    outline: OutlineData = Field(description="Presentation outline")
    slides: List[SlideData] = Field(
        default_factory=list,
        description="Generated slides"
    )
    total_slides: int = Field(description="Total number of slides")
    estimated_duration: Optional[int] = Field(
        None,
        description="Estimated duration in minutes"
    )
    telemetry: Optional[TelemetryData] = Field(
        None,
        description="Usage telemetry"
    )


# --- Agent Communication Models ---

class AgentMessage(BaseModel):
    """Message between agents."""
    message_id: str = Field(description="Message identifier")
    from_agent: str = Field(description="Source agent")
    to_agent: str = Field(description="Target agent")
    message_type: str = Field(description="Message type")
    payload: Any = Field(description="Message payload")
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for related messages"
    )
    reply_to: Optional[str] = Field(
        None,
        description="ID of message being replied to"
    )
    timestamp: float = Field(description="Message timestamp")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class AgentCapability(BaseModel):
    """Agent capability declaration."""
    capability_id: str = Field(description="Capability identifier")
    name: str = Field(description="Capability name")
    description: str = Field(description="Capability description")
    input_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="Input JSON schema"
    )
    output_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="Output JSON schema"
    )
    examples: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Usage examples"
    )


class AgentStatus(BaseModel):
    """Agent status information."""
    agent_id: str = Field(description="Agent identifier")
    status: str = Field(description="Current status")
    health: str = Field(description="Health status")
    capabilities: List[AgentCapability] = Field(
        default_factory=list,
        description="Agent capabilities"
    )
    active_tasks: int = Field(
        default=0,
        description="Number of active tasks"
    )
    total_processed: int = Field(
        default=0,
        description="Total tasks processed"
    )
    error_rate: float = Field(
        default=0.0,
        description="Error rate"
    )
    average_latency_ms: float = Field(
        default=0.0,
        description="Average latency in ms"
    )
    last_activity: Optional[float] = Field(
        None,
        description="Last activity timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional status data"
    )


# --- File and Asset Models ---

class FileType(str, Enum):
    """Supported file types."""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    TXT = "txt"
    MD = "md"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CSV = "csv"
    JSON = "json"
    UNKNOWN = "unknown"


class AssetData(BaseModel):
    """Asset/file data model."""
    asset_id: str = Field(description="Asset identifier")
    filename: str = Field(description="Original filename")
    file_type: FileType = Field(description="File type")
    mime_type: str = Field(description="MIME type")
    size_bytes: int = Field(description="File size in bytes")
    url: Optional[HttpUrl] = Field(None, description="Asset URL")
    content: Optional[str] = Field(None, description="Extracted text content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Asset metadata"
    )
    created_at: float = Field(description="Creation timestamp")
    processed: bool = Field(
        default=False,
        description="Whether asset has been processed"
    )


# --- Validation Utilities ---

def validate_trace_id(trace_id: str) -> str:
    """Validate trace ID format."""
    if not trace_id or len(trace_id) < 8:
        raise ValueError("Invalid trace ID")
    return trace_id


def validate_tokens(tokens: int) -> int:
    """Validate token count."""
    if tokens < 0:
        raise ValueError("Token count cannot be negative")
    if tokens > 1000000:
        raise ValueError("Token count exceeds maximum limit")
    return tokens


# --- Factory Functions ---

def create_error_response(
    trace_id: str,
    error_code: str,
    error_message: str,
    error_details: Optional[Dict[str, Any]] = None,
) -> ErrorResponse:
    """Create an error response."""
    return ErrorResponse(
        trace_id=trace_id,
        timestamp=datetime.utcnow().timestamp(),
        error_code=error_code,
        error_message=error_message,
        error_details=error_details,
    )


def create_success_response(
    trace_id: str,
    data: Any,
    duration_ms: Optional[int] = None,
) -> SuccessResponse:
    """Create a success response."""
    return SuccessResponse(
        trace_id=trace_id,
        timestamp=datetime.utcnow().timestamp(),
        data=data,
        duration_ms=duration_ms,
    )