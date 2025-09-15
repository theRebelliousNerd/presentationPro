"""
Configuration module for MCP Server

Handles environment variables, settings, and configuration management.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    """Server configuration settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server settings
    server_name: str = Field(
        default="PresentationPro MCP Server",
        description="Name of the MCP server",
    )
    server_version: str = Field(
        default="1.0.0",
        description="Server version",
    )
    protocol_version: str = Field(
        default="1.0",
        description="MCP protocol version",
    )

    # Network settings
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind the server",
    )
    port: int = Field(
        default=8090,
        description="Port to bind the server",
    )
    transport: str = Field(
        default="streamable-http",
        description="Transport mode (stdio, http, streamable-http)",
    )

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    log_file: Optional[str] = Field(
        default="/tmp/mcp_server.log",
        description="Log file path",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json, text)",
    )

    # Database settings
    arango_host: str = Field(
        default="localhost",
        env="ARANGO_HOST",
        description="ArangoDB host",
    )
    arango_port: int = Field(
        default=8529,
        env="ARANGO_PORT",
        description="ArangoDB port",
    )
    arango_database: str = Field(
        default="presentationpro",
        env="ARANGO_DATABASE",
        description="ArangoDB database name",
    )
    arango_username: Optional[str] = Field(
        default=None,
        env="ARANGO_USERNAME",
        description="ArangoDB username",
    )
    arango_password: Optional[str] = Field(
        default=None,
        env="ARANGO_PASSWORD",
        description="ArangoDB password",
    )

    # API keys
    google_genai_api_key: Optional[str] = Field(
        default=None,
        env="GOOGLE_GENAI_API_KEY",
        description="Google Generative AI API key",
    )
    bing_search_api_key: Optional[str] = Field(
        default=None,
        env="BING_SEARCH_API_KEY",
        description="Bing Search API key",
    )

    # Telemetry settings
    telemetry_enabled: bool = Field(
        default=True,
        description="Enable telemetry collection",
    )
    telemetry_sink: Optional[str] = Field(
        default="/tmp/mcp_telemetry.jsonl",
        env="MCP_TELEMETRY_SINK",
        description="Telemetry sink file path",
    )

    # Cache settings
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching",
    )
    cache_ttl: int = Field(
        default=3600,
        description="Cache TTL in seconds",
    )
    web_search_cache: Optional[str] = Field(
        default="/tmp/web_search_cache.json",
        env="WEB_SEARCH_CACHE",
        description="Web search cache file",
    )

    # Rate limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
    )
    rate_limit_requests: int = Field(
        default=100,
        description="Max requests per window",
    )
    rate_limit_window: int = Field(
        default=60,
        description="Rate limit window in seconds",
    )

    # Security settings
    auth_enabled: bool = Field(
        default=False,
        description="Enable authentication",
    )
    auth_token: Optional[str] = Field(
        default=None,
        env="MCP_AUTH_TOKEN",
        description="Authentication token",
    )
    cors_enabled: bool = Field(
        default=True,
        description="Enable CORS",
    )
    cors_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed CORS origins",
    )

    # Tool-specific settings
    max_search_results: int = Field(
        default=10,
        description="Maximum web search results",
    )
    max_rag_chunks: int = Field(
        default=5,
        description="Maximum RAG retrieval chunks",
    )
    max_asset_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum asset file size in bytes",
    )

    # Performance settings
    worker_threads: int = Field(
        default=4,
        description="Number of worker threads",
    )
    connection_timeout: int = Field(
        default=30,
        description="Connection timeout in seconds",
    )
    request_timeout: int = Field(
        default=60,
        description="Request timeout in seconds",
    )

    # Feature flags
    enable_batch_operations: bool = Field(
        default=True,
        description="Enable batch tool operations",
    )
    enable_streaming: bool = Field(
        default=True,
        description="Enable streaming responses",
    )
    enable_composite_tools: bool = Field(
        default=True,
        description="Enable composite tool operations",
    )

    def get_arango_url(self) -> str:
        """Get ArangoDB connection URL"""
        if self.arango_username and self.arango_password:
            return f"http://{self.arango_username}:{self.arango_password}@{self.arango_host}:{self.arango_port}"
        return f"http://{self.arango_host}:{self.arango_port}"

    def get_capabilities(self) -> List[str]:
        """Get server capabilities"""
        capabilities = ["tools", "telemetry", "versioning"]

        if self.enable_batch_operations:
            capabilities.append("batch")
        if self.enable_streaming:
            capabilities.append("streaming")
        if self.auth_enabled:
            capabilities.append("authentication")
        if self.rate_limit_enabled:
            capabilities.append("rateLimit")

        return capabilities

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (excluding sensitive data)"""
        data = self.model_dump()

        # Remove sensitive fields
        sensitive_fields = [
            "google_genai_api_key",
            "bing_search_api_key",
            "arango_password",
            "auth_token",
        ]

        for field in sensitive_fields:
            if field in data:
                data[field] = "***" if data[field] else None

        return data


# Global settings instance
settings = ServerSettings()


def get_settings() -> ServerSettings:
    """Get the global settings instance"""
    return settings


def update_settings(**kwargs) -> ServerSettings:
    """Update settings with new values"""
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    return settings