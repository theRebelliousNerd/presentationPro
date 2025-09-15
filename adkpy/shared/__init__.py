"""
Shared Utilities Package

Common utilities and schemas used across all agents.
"""

from .config import (
    Config,
    get_config,
    load_config,
    AgentConfig,
    SystemConfig,
)
from .logging_config import (
    setup_logging,
    get_logger,
    log_timing,
    log_error,
    LogContext,
)
from .schemas import (
    # Base schemas
    BaseRequest,
    BaseResponse,
    ErrorResponse,
    SuccessResponse,
    # Telemetry
    TelemetryData,
    MetricsData,
    # Presentation schemas
    PresentationRequest,
    PresentationResponse,
    SlideData,
    OutlineData,
)
from .telemetry import (
    TelemetryTracker,
    track_usage,
    track_event,
    track_error,
    get_telemetry_summary,
)
from .mcp_client import (
    MCPClient,
    MCPToolResult,
    get_mcp_client,
    cleanup_mcp_client,
)

__all__ = [
    # Config
    "Config",
    "get_config",
    "load_config",
    "AgentConfig",
    "SystemConfig",
    # Logging
    "setup_logging",
    "get_logger",
    "log_timing",
    "log_error",
    "LogContext",
    # Schemas
    "BaseRequest",
    "BaseResponse",
    "ErrorResponse",
    "SuccessResponse",
    "TelemetryData",
    "MetricsData",
    "PresentationRequest",
    "PresentationResponse",
    "SlideData",
    "OutlineData",
    # Telemetry
    "TelemetryTracker",
    "track_usage",
    "track_event",
    "track_error",
    "get_telemetry_summary",
    # MCP Client
    "MCPClient",
    "MCPToolResult",
    "get_mcp_client",
    "cleanup_mcp_client",
]