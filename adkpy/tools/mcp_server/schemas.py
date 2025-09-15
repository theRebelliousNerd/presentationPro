"""
MCP Protocol Schemas

Defines the request/response models and data structures for the MCP protocol.
Based on the Model Context Protocol specification.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# Base MCP Protocol Types

class ContentType(str, Enum):
    """Content types for MCP messages"""
    TEXT = "text"
    IMAGE = "image"
    RESOURCE = "resource"
    ERROR = "error"


class Content(BaseModel):
    """Base content model"""
    type: ContentType
    text: Optional[str] = None
    data: Optional[str] = None  # Base64 encoded for images
    mimeType: Optional[str] = None
    uri: Optional[str] = None


class TextContent(BaseModel):
    """Text content"""
    type: str = "text"
    text: str


class ImageContent(BaseModel):
    """Image content"""
    type: str = "image"
    data: str  # Base64 encoded
    mimeType: str = "image/png"


class ResourceContent(BaseModel):
    """Resource content"""
    type: str = "resource"
    uri: str
    text: Optional[str] = None
    mimeType: Optional[str] = None


# Tool-specific schemas

class ToolParameter(BaseModel):
    """Tool parameter definition"""
    name: str
    type: str  # JSON Schema type
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    pattern: Optional[str] = None


class ToolDefinition(BaseModel):
    """Tool definition for MCP protocol"""
    name: str
    description: str
    inputSchema: Dict[str, Any]  # JSON Schema
    category: Optional[str] = "general"
    version: Optional[str] = "1.0.0"
    deprecated: bool = False
    deprecationMessage: Optional[str] = None
    performanceHint: Optional[str] = "fast"  # fast, moderate, slow
    examples: List[Dict[str, Any]] = Field(default_factory=list)


# Request/Response models

class MCPRequest(BaseModel):
    """Base MCP request"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """Base MCP response"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class ListToolsRequest(BaseModel):
    """Request to list available tools"""
    category: Optional[str] = None
    includeDeprecated: bool = False


class ListToolsResponse(BaseModel):
    """Response with list of tools"""
    tools: List[ToolDefinition]


class CallToolRequest(BaseModel):
    """Request to call a tool"""
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class CallToolResponse(BaseModel):
    """Response from tool call"""
    name: str
    content: List[Union[TextContent, ImageContent, ResourceContent]]
    isError: bool = False


class ErrorResponse(BaseModel):
    """Error response"""
    code: int
    message: str
    data: Optional[Any] = None


# Health and monitoring

class HealthResponse(BaseModel):
    """Health check response"""
    status: str  # healthy, degraded, unhealthy
    server_name: str
    tools_count: int
    uptime_seconds: int
    version: Optional[str] = "1.0.0"
    errors: List[str] = Field(default_factory=list)


# Telemetry schemas

class TelemetryRequest(BaseModel):
    """Telemetry recording request"""
    step: str
    agent: Optional[str] = None
    model: Optional[str] = None
    promptTokens: int = 0
    completionTokens: int = 0
    durationMs: int = 0
    cost: Optional[float] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class TelemetryResponse(BaseModel):
    """Telemetry response"""
    ok: bool
    event: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TelemetryAggregateResponse(BaseModel):
    """Aggregated telemetry statistics"""
    total: Dict[str, Any]
    byAgent: Dict[str, Dict[str, Any]]
    timeRange: Optional[Dict[str, Any]] = None


# RAG/Search schemas

class IngestRequest(BaseModel):
    """Document ingestion request"""
    presentationId: str
    assets: List[Dict[str, Any]]


class IngestResponse(BaseModel):
    """Document ingestion response"""
    ok: bool
    docs: int
    chunks: int
    warnings: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class RetrieveRequest(BaseModel):
    """Document retrieval request"""
    presentationId: str
    query: str
    limit: int = 5
    filters: Optional[Dict[str, Any]] = None


class RetrieveResponse(BaseModel):
    """Document retrieval response"""
    chunks: List[Dict[str, Any]]
    count: int
    error: Optional[str] = None


class SearchRequest(BaseModel):
    """Web search request"""
    query: str
    top_k: int = 5
    allow_domains: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Web search response"""
    results: List[Dict[str, str]]
    count: int
    error: Optional[str] = None


# Vision schemas

class VisionAnalyzeRequest(BaseModel):
    """Vision analysis request"""
    screenshotDataUrl: str
    analysisType: str = "contrast"  # contrast, ocr, object_detection


class VisionAnalyzeResponse(BaseModel):
    """Vision analysis response"""
    mean: Optional[float] = None
    variance: Optional[float] = None
    recommendDarken: Optional[bool] = None
    overlay: Optional[float] = None
    text: Optional[str] = None  # For OCR
    objects: Optional[List[Dict[str, Any]]] = None  # For object detection
    error: Optional[str] = None


# Authentication schemas

class AuthRequest(BaseModel):
    """Authentication request"""
    token: Optional[str] = None
    apiKey: Optional[str] = None


class AuthResponse(BaseModel):
    """Authentication response"""
    authenticated: bool
    user: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    expiresAt: Optional[int] = None


# Session management

class SessionRequest(BaseModel):
    """Session initialization request"""
    clientName: str
    clientVersion: str
    protocolVersion: str = "1.0"
    capabilities: List[str] = Field(default_factory=list)


class SessionResponse(BaseModel):
    """Session initialization response"""
    sessionId: str
    serverName: str
    serverVersion: str
    protocolVersion: str
    capabilities: List[str]


# Batch operations

class BatchRequest(BaseModel):
    """Batch operation request"""
    operations: List[Dict[str, Any]]
    parallel: bool = False
    continueOnError: bool = True


class BatchResponse(BaseModel):
    """Batch operation response"""
    results: List[Dict[str, Any]]
    succeeded: int
    failed: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# Streaming schemas

class StreamRequest(BaseModel):
    """Stream request"""
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)
    streamId: Optional[str] = None


class StreamChunk(BaseModel):
    """Stream chunk"""
    streamId: str
    sequence: int
    data: Any
    isLast: bool = False


class StreamComplete(BaseModel):
    """Stream completion"""
    streamId: str
    totalChunks: int
    duration: int  # milliseconds


# Rate limiting

class RateLimitInfo(BaseModel):
    """Rate limit information"""
    limit: int  # requests per window
    remaining: int
    reset: int  # Unix timestamp
    window: str  # e.g., "1m", "1h"


# Versioning

class VersionInfo(BaseModel):
    """Version information"""
    server: str
    protocol: str
    tools: Dict[str, str]  # tool name -> version
    deprecated: List[str] = Field(default_factory=list)
    beta: List[str] = Field(default_factory=list)


# Capability discovery

class CapabilityInfo(BaseModel):
    """Server capability information"""
    tools: bool = True
    resources: bool = False
    prompts: bool = False
    streaming: bool = True
    batch: bool = True
    telemetry: bool = True
    authentication: bool = False
    rateLimit: bool = True
    versioning: bool = True


# Error codes

class ErrorCode(int, Enum):
    """Standard MCP error codes"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # Custom error codes
    AUTHENTICATION_REQUIRED = -32000
    PERMISSION_DENIED = -32001
    RATE_LIMIT_EXCEEDED = -32002
    TOOL_NOT_FOUND = -32003
    TOOL_EXECUTION_ERROR = -32004
    RESOURCE_NOT_FOUND = -32005
    SESSION_EXPIRED = -32006
    INVALID_SESSION = -32007
    DEPRECATED_METHOD = -32008
    BETA_FEATURE = -32009


# Composite responses

class ToolExecutionResult(BaseModel):
    """Complete tool execution result"""
    request: CallToolRequest
    response: CallToolResponse
    telemetry: Optional[TelemetryResponse] = None
    rateLimit: Optional[RateLimitInfo] = None
    duration: int  # milliseconds


class MultiToolResponse(BaseModel):
    """Response from multiple tool executions"""
    results: List[ToolExecutionResult]
    telemetry: TelemetryAggregateResponse
    errors: List[ErrorResponse] = Field(default_factory=list)