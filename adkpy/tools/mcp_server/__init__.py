"""
MCP Server for PresentationPro Tools

A production-ready Model Context Protocol server that exposes all ADK tools
through a standardized interface.
"""

from .config import ServerSettings, get_settings, update_settings
from .schemas import (
    CallToolRequest,
    CallToolResponse,
    ErrorResponse,
    HealthResponse,
    ListToolsRequest,
    ListToolsResponse,
    ToolDefinition,
)
from .server import MCPServer
from .tool_registry import ToolRegistry
from .tool_wrappers import (
    ArangoRAGWrapper,
    AssetsWrapper,
    CompositeToolWrapper,
    TelemetryWrapper,
    VisionWrapper,
    WebSearchWrapper,
    DesignWrapper,
)

__version__ = "1.0.0"

__all__ = [
    # Server
    "MCPServer",
    # Registry
    "ToolRegistry",
    # Wrappers
    "ArangoRAGWrapper",
    "WebSearchWrapper",
    "VisionWrapper",
    "TelemetryWrapper",
    "AssetsWrapper",
    "CompositeToolWrapper",
    "DesignWrapper",
    # Schemas
    "ToolDefinition",
    "ListToolsRequest",
    "ListToolsResponse",
    "CallToolRequest",
    "CallToolResponse",
    "ErrorResponse",
    "HealthResponse",
    # Config
    "ServerSettings",
    "get_settings",
    "update_settings",
]
