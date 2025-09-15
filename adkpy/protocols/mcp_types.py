"""
MCP Protocol Type Definitions

Type definitions for the Model Context Protocol (MCP).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl


# --- MCP Protocol Version ---

MCP_PROTOCOL_VERSION = "2024-11-05"


# --- MCP Methods ---

class MCPMethod(str, Enum):
    """MCP protocol methods."""
    # Tool methods
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    # Resource methods
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"
    RESOURCES_UNSUBSCRIBE = "resources/unsubscribe"
    # Prompt methods
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    # Completion methods
    COMPLETION_COMPLETE = "completion/complete"
    # Logging methods
    LOGGING_SET_LEVEL = "logging/setLevel"
    # Ping
    PING = "ping"


# --- MCP Base Models ---

class MCPRequest(BaseModel):
    """MCP JSON-RPC request."""
    jsonrpc: str = Field(
        default="2.0",
        description="JSON-RPC version"
    )
    id: Union[str, int] = Field(
        description="Request ID"
    )
    method: str = Field(
        description="MCP method"
    )
    params: Optional[Dict[str, Any]] = Field(
        None,
        description="Method parameters"
    )


class MCPError(BaseModel):
    """MCP error object."""
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


class MCPResponse(BaseModel):
    """MCP JSON-RPC response."""
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
    error: Optional[MCPError] = Field(
        None,
        description="Error object (if error)"
    )


# --- Tool Models ---

class MCPToolInputSchema(BaseModel):
    """Tool input schema."""
    type: str = Field(
        default="object",
        description="Schema type"
    )
    properties: Dict[str, Dict[str, Any]] = Field(
        description="Property definitions"
    )
    required: Optional[List[str]] = Field(
        None,
        description="Required properties"
    )
    additionalProperties: Optional[bool] = Field(
        None,
        description="Allow additional properties"
    )


class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str = Field(
        description="Tool name"
    )
    description: str = Field(
        description="Tool description"
    )
    inputSchema: MCPToolInputSchema = Field(
        description="Input schema"
    )


class MCPToolCall(BaseModel):
    """Tool call request."""
    name: str = Field(
        description="Tool name"
    )
    arguments: Dict[str, Any] = Field(
        description="Tool arguments"
    )


class MCPToolResult(BaseModel):
    """Tool call result."""
    content: List[Dict[str, Any]] = Field(
        description="Result content"
    )
    isError: Optional[bool] = Field(
        None,
        description="Whether result is an error"
    )


# --- Resource Models ---

class MCPResource(BaseModel):
    """MCP resource definition."""
    uri: str = Field(
        description="Resource URI"
    )
    name: str = Field(
        description="Resource name"
    )
    description: Optional[str] = Field(
        None,
        description="Resource description"
    )
    mimeType: Optional[str] = Field(
        None,
        description="Resource MIME type"
    )


class MCPResourceContent(BaseModel):
    """Resource content."""
    uri: str = Field(
        description="Resource URI"
    )
    mimeType: Optional[str] = Field(
        None,
        description="Content MIME type"
    )
    text: Optional[str] = Field(
        None,
        description="Text content"
    )
    blob: Optional[str] = Field(
        None,
        description="Base64-encoded binary content"
    )


class MCPResourceSubscription(BaseModel):
    """Resource subscription."""
    uri: str = Field(
        description="Resource URI"
    )
    subscriptionId: str = Field(
        description="Subscription ID"
    )


# --- Prompt Models ---

class MCPPromptArgument(BaseModel):
    """Prompt argument definition."""
    name: str = Field(
        description="Argument name"
    )
    description: Optional[str] = Field(
        None,
        description="Argument description"
    )
    required: Optional[bool] = Field(
        None,
        description="Whether argument is required"
    )


class MCPPrompt(BaseModel):
    """MCP prompt definition."""
    name: str = Field(
        description="Prompt name"
    )
    description: Optional[str] = Field(
        None,
        description="Prompt description"
    )
    arguments: Optional[List[MCPPromptArgument]] = Field(
        None,
        description="Prompt arguments"
    )


class MCPPromptMessage(BaseModel):
    """Prompt message."""
    role: str = Field(
        description="Message role (user, assistant, system)"
    )
    content: Union[str, List[Dict[str, Any]]] = Field(
        description="Message content"
    )


class MCPPromptResult(BaseModel):
    """Prompt result."""
    description: Optional[str] = Field(
        None,
        description="Result description"
    )
    messages: List[MCPPromptMessage] = Field(
        description="Prompt messages"
    )


# --- Completion Models ---

class MCPCompletionArgument(BaseModel):
    """Completion argument."""
    name: str = Field(
        description="Argument name"
    )
    value: str = Field(
        description="Argument value"
    )


class MCPCompletionRequest(BaseModel):
    """Completion request."""
    ref: Union[str, Dict[str, Any]] = Field(
        description="Completion reference"
    )
    argument: MCPCompletionArgument = Field(
        description="Completion argument"
    )


class MCPCompletionResult(BaseModel):
    """Completion result."""
    completion: Union[str, Dict[str, Any]] = Field(
        description="Completion text or structured data"
    )
    isComplete: Optional[bool] = Field(
        None,
        description="Whether completion is complete"
    )
    hasMore: Optional[bool] = Field(
        None,
        description="Whether more completions are available"
    )


# --- Logging Models ---

class MCPLogLevel(str, Enum):
    """MCP log levels."""
    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"


class MCPLoggingMessage(BaseModel):
    """Logging message."""
    level: MCPLogLevel = Field(
        description="Log level"
    )
    logger: Optional[str] = Field(
        None,
        description="Logger name"
    )
    data: Any = Field(
        description="Log data"
    )


# --- Notification Models ---

class MCPNotification(BaseModel):
    """MCP notification."""
    jsonrpc: str = Field(
        default="2.0",
        description="JSON-RPC version"
    )
    method: str = Field(
        description="Notification method"
    )
    params: Optional[Dict[str, Any]] = Field(
        None,
        description="Notification parameters"
    )


class MCPProgressNotification(BaseModel):
    """Progress notification."""
    progressToken: Union[str, int] = Field(
        description="Progress token"
    )
    progress: float = Field(
        description="Progress percentage (0-100)"
    )
    total: Optional[float] = Field(
        None,
        description="Total work units"
    )


class MCPResourceUpdatedNotification(BaseModel):
    """Resource updated notification."""
    uri: str = Field(
        description="Resource URI"
    )


class MCPCancelledNotification(BaseModel):
    """Cancelled notification."""
    requestId: Union[str, int] = Field(
        description="Cancelled request ID"
    )
    reason: Optional[str] = Field(
        None,
        description="Cancellation reason"
    )


# --- Server Info Models ---

class MCPServerInfo(BaseModel):
    """MCP server information."""
    name: str = Field(
        description="Server name"
    )
    version: str = Field(
        description="Server version"
    )
    protocolVersion: str = Field(
        default=MCP_PROTOCOL_VERSION,
        description="MCP protocol version"
    )
    capabilities: Optional[Dict[str, Any]] = Field(
        None,
        description="Server capabilities"
    )


class MCPImplementation(BaseModel):
    """MCP implementation info."""
    name: str = Field(
        description="Implementation name"
    )
    version: str = Field(
        description="Implementation version"
    )


class MCPInitializeRequest(BaseModel):
    """Initialize request."""
    protocolVersion: str = Field(
        default=MCP_PROTOCOL_VERSION,
        description="Client protocol version"
    )
    capabilities: Dict[str, Any] = Field(
        description="Client capabilities"
    )
    clientInfo: MCPImplementation = Field(
        description="Client implementation info"
    )


class MCPInitializeResult(BaseModel):
    """Initialize result."""
    protocolVersion: str = Field(
        default=MCP_PROTOCOL_VERSION,
        description="Server protocol version"
    )
    capabilities: Dict[str, Any] = Field(
        description="Server capabilities"
    )
    serverInfo: MCPImplementation = Field(
        description="Server implementation info"
    )