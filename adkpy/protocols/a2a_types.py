"""
A2A Protocol Type Definitions

Type definitions for the Agent-to-Agent (A2A) protocol.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl


# --- A2A Protocol Version ---

A2A_PROTOCOL_VERSION = "0.2.6"


# --- A2A Methods ---

class A2AMethod(str, Enum):
    """A2A protocol methods."""
    # Task methods
    TASKS_SEND = "tasks/send"
    TASKS_STATUS = "tasks/status"
    TASKS_CANCEL = "tasks/cancel"
    TASKS_STREAM = "tasks/stream"
    TASKS_LIST = "tasks/list"
    # Agent methods
    AGENT_INFO = "agent/info"
    AGENT_HEALTH = "agent/health"
    AGENT_CAPABILITIES = "agent/capabilities"
    # Session methods
    SESSION_CREATE = "session/create"
    SESSION_UPDATE = "session/update"
    SESSION_DELETE = "session/delete"
    SESSION_LIST = "session/list"


# --- A2A Error Codes ---

class A2AErrorCode(int, Enum):
    """A2A error codes (JSON-RPC compatible)."""
    # Standard JSON-RPC errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    # A2A specific errors
    AGENT_NOT_FOUND = -32000
    TASK_NOT_FOUND = -32001
    SESSION_NOT_FOUND = -32002
    AUTHENTICATION_REQUIRED = -32003
    AUTHORIZATION_FAILED = -32004
    RATE_LIMIT_EXCEEDED = -32005
    TASK_TIMEOUT = -32006
    TASK_CANCELLED = -32007
    AGENT_UNAVAILABLE = -32008
    INVALID_AGENT_CARD = -32009


# --- A2A Base Models ---

class A2ARequest(BaseModel):
    """A2A JSON-RPC request."""
    jsonrpc: str = Field(
        default="2.0",
        description="JSON-RPC version"
    )
    id: Union[str, int] = Field(
        description="Request ID"
    )
    method: str = Field(
        description="A2A method"
    )
    params: Optional[Dict[str, Any]] = Field(
        None,
        description="Method parameters"
    )


class A2AError(BaseModel):
    """A2A error object."""
    code: int = Field(
        description="Error code"
    )
    message: str = Field(
        description="Error message"
    )
    data: Optional[Any] = Field(
        None,
        description="Additional error data"
    )


class A2AResponse(BaseModel):
    """A2A JSON-RPC response."""
    jsonrpc: str = Field(
        default="2.0",
        description="JSON-RPC version"
    )
    id: Union[str, int, None] = Field(
        description="Request ID"
    )
    result: Optional[Any] = Field(
        None,
        description="Result data (if success)"
    )
    error: Optional[A2AError] = Field(
        None,
        description="Error object (if error)"
    )


# --- Task Models ---

class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskRequest(BaseModel):
    """Task request for A2A protocol."""
    task_id: str = Field(
        description="Unique task identifier"
    )
    input: Any = Field(
        description="Task input data"
    )
    priority: TaskPriority = Field(
        default=TaskPriority.NORMAL,
        description="Task priority"
    )
    timeout: Optional[int] = Field(
        None,
        description="Task timeout in seconds"
    )
    session_id: Optional[str] = Field(
        None,
        description="Session ID for stateful operations"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata"
    )


class TaskResponse(BaseModel):
    """Task response for A2A protocol."""
    task_id: str = Field(
        description="Task identifier"
    )
    status: TaskStatus = Field(
        description="Task status"
    )
    result: Optional[Any] = Field(
        None,
        description="Task result (if completed)"
    )
    error: Optional[str] = Field(
        None,
        description="Error message (if failed)"
    )
    progress: Optional[float] = Field(
        None,
        description="Progress percentage (0-100)"
    )
    created_at: float = Field(
        description="Creation timestamp"
    )
    updated_at: float = Field(
        description="Last update timestamp"
    )
    completed_at: Optional[float] = Field(
        None,
        description="Completion timestamp"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata"
    )


# --- Agent Card Models ---

class AgentAuthentication(BaseModel):
    """Authentication requirements."""
    type: str = Field(
        description="Authentication type"
    )
    schemes: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Authentication schemes (OpenAPI format)"
    )


class AgentCapabilities(BaseModel):
    """Agent capabilities."""
    supports_streaming: bool = Field(
        default=False,
        description="Supports streaming responses"
    )
    supports_stateless: bool = Field(
        default=True,
        description="Supports stateless operations"
    )
    supports_sessions: bool = Field(
        default=False,
        description="Supports session management"
    )
    supports_batch: bool = Field(
        default=False,
        description="Supports batch operations"
    )
    max_concurrent_tasks: int = Field(
        default=10,
        description="Maximum concurrent tasks"
    )
    timeout: int = Field(
        default=300,
        description="Default timeout in seconds"
    )
    supported_protocol_versions: List[str] = Field(
        default_factory=lambda: [A2A_PROTOCOL_VERSION],
        description="Supported A2A protocol versions"
    )


class AgentSkill(BaseModel):
    """Agent skill declaration."""
    id: str = Field(
        description="Unique skill identifier"
    )
    name: str = Field(
        description="Human-readable skill name"
    )
    description: str = Field(
        description="Detailed skill description"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Skill tags"
    )
    examples: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Usage examples"
    )
    input_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON Schema for input"
    )
    output_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON Schema for output"
    )
    cost: Optional[Dict[str, Any]] = Field(
        None,
        description="Cost information"
    )


class AgentCard(BaseModel):
    """Agent card for discovery and metadata."""
    name: str = Field(
        description="Agent name"
    )
    version: str = Field(
        description="Agent version"
    )
    description: str = Field(
        description="Agent description"
    )
    url: HttpUrl = Field(
        description="Agent endpoint URL"
    )
    skills: List[AgentSkill] = Field(
        default_factory=list,
        description="Agent skills"
    )
    capabilities: AgentCapabilities = Field(
        default_factory=AgentCapabilities,
        description="Agent capabilities"
    )
    authentication: Optional[AgentAuthentication] = Field(
        None,
        description="Authentication requirements"
    )
    default_input_modes: List[str] = Field(
        default_factory=lambda: ["text/plain", "application/json"],
        description="Supported input MIME types"
    )
    default_output_modes: List[str] = Field(
        default_factory=lambda: ["application/json"],
        description="Supported output MIME types"
    )
    protocol_version: str = Field(
        default=A2A_PROTOCOL_VERSION,
        description="A2A protocol version"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    contact: Optional[Dict[str, str]] = Field(
        None,
        description="Contact information"
    )
    documentation: Optional[HttpUrl] = Field(
        None,
        description="Documentation URL"
    )
    terms_of_service: Optional[HttpUrl] = Field(
        None,
        description="Terms of service URL"
    )


# --- Session Models ---

class SessionRequest(BaseModel):
    """Session creation request."""
    session_id: Optional[str] = Field(
        None,
        description="Session ID (generated if not provided)"
    )
    user_id: Optional[str] = Field(
        None,
        description="User identifier"
    )
    ttl: Optional[int] = Field(
        None,
        description="Session TTL in seconds"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Session metadata"
    )


class SessionResponse(BaseModel):
    """Session response."""
    session_id: str = Field(
        description="Session identifier"
    )
    created_at: float = Field(
        description="Creation timestamp"
    )
    expires_at: Optional[float] = Field(
        None,
        description="Expiration timestamp"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Session metadata"
    )


# --- Health Check Models ---

class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Health check response."""
    status: HealthStatus = Field(
        description="Health status"
    )
    agent: str = Field(
        description="Agent name"
    )
    version: str = Field(
        description="Agent version"
    )
    uptime: float = Field(
        description="Uptime in seconds"
    )
    active_tasks: int = Field(
        description="Number of active tasks"
    )
    total_processed: int = Field(
        description="Total tasks processed"
    )
    error_rate: float = Field(
        description="Error rate (0-1)"
    )
    checks: Optional[Dict[str, bool]] = Field(
        None,
        description="Individual health checks"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional health data"
    )