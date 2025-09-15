"""
Configuration Management

Centralized configuration for the A2A system.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

# Configuration file paths
CONFIG_DIR = Path(__file__).parent.parent / "config"
DEFAULT_CONFIG_FILE = CONFIG_DIR / "default.yaml"
LOCAL_CONFIG_FILE = CONFIG_DIR / "local.yaml"
ENV_PREFIX = "ADK_"


# --- Configuration Models ---

class ModelConfig(BaseModel):
    """Model configuration."""
    name: str = Field(description="Model name")
    provider: str = Field(default="googleai", description="Model provider")
    temperature: float = Field(default=0.7, description="Temperature")
    max_tokens: Optional[int] = Field(None, description="Max tokens")
    top_p: Optional[float] = Field(None, description="Top P")
    top_k: Optional[int] = Field(None, description="Top K")
    timeout: int = Field(default=60, description="Request timeout")


class AgentConfig(BaseModel):
    """Individual agent configuration."""
    name: str = Field(description="Agent name")
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    model: ModelConfig = Field(description="Model configuration")
    max_concurrent_tasks: int = Field(
        default=10,
        description="Maximum concurrent tasks"
    )
    task_timeout: int = Field(
        default=300,
        description="Task timeout in seconds"
    )
    retry_policy: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_attempts": 3,
            "base_delay": 1.0,
            "max_delay": 60.0,
        },
        description="Retry policy configuration"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional agent metadata"
    )


class SystemConfig(BaseModel):
    """System-wide configuration."""
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    port: int = Field(
        default=8089,
        description="Server port"
    )
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    cors_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="CORS allowed origins"
    )
    max_request_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum request size in bytes"
    )
    request_timeout: int = Field(
        default=300,
        description="Global request timeout"
    )


class DatabaseConfig(BaseModel):
    """Database configuration."""
    type: str = Field(default="arangodb", description="Database type")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=8529, description="Database port")
    username: Optional[str] = Field(None, description="Database username")
    password: Optional[str] = Field(None, description="Database password")
    database: str = Field(default="presentationpro", description="Database name")
    pool_size: int = Field(default=10, description="Connection pool size")


class TelemetryConfig(BaseModel):
    """Telemetry configuration."""
    enabled: bool = Field(default=True, description="Enable telemetry")
    export_interval: int = Field(
        default=60,
        description="Export interval in seconds"
    )
    max_events: int = Field(
        default=10000,
        description="Maximum events to store"
    )
    export_endpoint: Optional[str] = Field(
        None,
        description="Telemetry export endpoint"
    )


class SecurityConfig(BaseModel):
    """Security configuration."""
    enable_auth: bool = Field(
        default=False,
        description="Enable authentication"
    )
    auth_type: str = Field(
        default="bearer",
        description="Authentication type"
    )
    api_keys: List[str] = Field(
        default_factory=list,
        description="Valid API keys"
    )
    jwt_secret: Optional[str] = Field(
        None,
        description="JWT secret for token validation"
    )
    rate_limiting: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": True,
            "requests_per_minute": 60,
            "burst": 10,
        },
        description="Rate limiting configuration"
    )


class Config(BaseModel):
    """Complete application configuration."""
    system: SystemConfig = Field(
        default_factory=SystemConfig,
        description="System configuration"
    )
    agents: Dict[str, AgentConfig] = Field(
        default_factory=dict,
        description="Agent configurations"
    )
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig,
        description="Database configuration"
    )
    telemetry: TelemetryConfig = Field(
        default_factory=TelemetryConfig,
        description="Telemetry configuration"
    )
    security: SecurityConfig = Field(
        default_factory=SecurityConfig,
        description="Security configuration"
    )
    api_keys: Dict[str, str] = Field(
        default_factory=dict,
        description="External API keys"
    )


# --- Configuration Manager ---

class ConfigManager:
    """Manages application configuration."""

    _instance: Optional[ConfigManager] = None
    _config: Optional[Config] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def load_config(
        cls,
        config_file: Optional[Path] = None,
        override_env: bool = True,
    ) -> Config:
        """
        Load configuration from file and environment.

        Args:
            config_file: Configuration file path
            override_env: Whether to override with environment variables

        Returns:
            Loaded configuration
        """
        config_data = {}

        # Load default configuration
        if DEFAULT_CONFIG_FILE.exists():
            with open(DEFAULT_CONFIG_FILE, "r") as f:
                if DEFAULT_CONFIG_FILE.suffix == ".yaml":
                    default_data = yaml.safe_load(f)
                else:
                    default_data = json.load(f)
                config_data = deep_merge(config_data, default_data or {})

        # Load local configuration
        if LOCAL_CONFIG_FILE.exists():
            with open(LOCAL_CONFIG_FILE, "r") as f:
                if LOCAL_CONFIG_FILE.suffix == ".yaml":
                    local_data = yaml.safe_load(f)
                else:
                    local_data = json.load(f)
                config_data = deep_merge(config_data, local_data or {})

        # Load specified configuration file
        if config_file and config_file.exists():
            with open(config_file, "r") as f:
                if config_file.suffix == ".yaml":
                    file_data = yaml.safe_load(f)
                else:
                    file_data = json.load(f)
                config_data = deep_merge(config_data, file_data or {})

        # Override with environment variables
        if override_env:
            config_data = cls._apply_env_overrides(config_data)

        # Create configuration object
        cls._config = Config(**config_data)

        return cls._config

    @classmethod
    def _apply_env_overrides(cls, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides."""
        # System configuration
        if env_val := os.getenv(f"{ENV_PREFIX}ENVIRONMENT"):
            config_data.setdefault("system", {})["environment"] = env_val

        if env_val := os.getenv(f"{ENV_PREFIX}DEBUG"):
            config_data.setdefault("system", {})["debug"] = env_val.lower() == "true"

        if env_val := os.getenv(f"{ENV_PREFIX}LOG_LEVEL"):
            config_data.setdefault("system", {})["log_level"] = env_val

        if env_val := os.getenv(f"{ENV_PREFIX}PORT"):
            config_data.setdefault("system", {})["port"] = int(env_val)

        # Database configuration
        if env_val := os.getenv(f"{ENV_PREFIX}DB_HOST"):
            config_data.setdefault("database", {})["host"] = env_val

        if env_val := os.getenv(f"{ENV_PREFIX}DB_PORT"):
            config_data.setdefault("database", {})["port"] = int(env_val)

        if env_val := os.getenv(f"{ENV_PREFIX}DB_USERNAME"):
            config_data.setdefault("database", {})["username"] = env_val

        if env_val := os.getenv(f"{ENV_PREFIX}DB_PASSWORD"):
            config_data.setdefault("database", {})["password"] = env_val

        # API keys
        if env_val := os.getenv("GOOGLE_GENAI_API_KEY"):
            config_data.setdefault("api_keys", {})["google_genai"] = env_val

        if env_val := os.getenv("BING_SEARCH_API_KEY"):
            config_data.setdefault("api_keys", {})["bing_search"] = env_val

        if env_val := os.getenv("OPENAI_API_KEY"):
            config_data.setdefault("api_keys", {})["openai"] = env_val

        # Security
        if env_val := os.getenv(f"{ENV_PREFIX}ENABLE_AUTH"):
            config_data.setdefault("security", {})["enable_auth"] = env_val.lower() == "true"

        if env_val := os.getenv(f"{ENV_PREFIX}JWT_SECRET"):
            config_data.setdefault("security", {})["jwt_secret"] = env_val

        if env_val := os.getenv(f"{ENV_PREFIX}API_KEYS"):
            config_data.setdefault("security", {})["api_keys"] = env_val.split(",")

        return config_data

    @classmethod
    def get_config(cls) -> Config:
        """Get current configuration."""
        if cls._config is None:
            cls._config = cls.load_config()
        return cls._config

    @classmethod
    def get_agent_config(cls, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for specific agent."""
        config = cls.get_config()
        return config.agents.get(agent_name)

    @classmethod
    def update_config(cls, updates: Dict[str, Any]):
        """Update configuration at runtime."""
        if cls._config is None:
            cls.get_config()

        # Apply updates
        config_dict = cls._config.model_dump()
        config_dict = deep_merge(config_dict, updates)
        cls._config = Config(**config_dict)

    @classmethod
    def save_config(cls, config_file: Path):
        """Save current configuration to file."""
        if cls._config is None:
            raise ValueError("No configuration loaded")

        config_data = cls._config.model_dump()

        with open(config_file, "w") as f:
            if config_file.suffix == ".yaml":
                yaml.safe_dump(config_data, f, default_flow_style=False)
            else:
                json.dump(config_data, f, indent=2)


# --- Utility Functions ---

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Override dictionary

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def get_config() -> Config:
    """Get current configuration."""
    return ConfigManager.get_config()


def load_config(config_file: Optional[Path] = None) -> Config:
    """Load configuration."""
    return ConfigManager.load_config(config_file)


def get_agent_config(agent_name: str) -> Optional[AgentConfig]:
    """Get agent configuration."""
    return ConfigManager.get_agent_config(agent_name)


# --- Default Agent Configurations ---

DEFAULT_AGENTS = {
    "clarifier": AgentConfig(
        name="clarifier",
        model=ModelConfig(
            name="gemini-2.5-flash",
            temperature=0.7,
        ),
        max_concurrent_tasks=5,
    ),
    "outline": AgentConfig(
        name="outline",
        model=ModelConfig(
            name="gemini-2.5-flash",
            temperature=0.5,
        ),
        max_concurrent_tasks=3,
    ),
    "slide_writer": AgentConfig(
        name="slide_writer",
        model=ModelConfig(
            name="gemini-2.5-flash",
            temperature=0.7,
        ),
        max_concurrent_tasks=10,
    ),
    "critic": AgentConfig(
        name="critic",
        model=ModelConfig(
            name="gemini-2.5-flash",
            temperature=0.3,
        ),
        max_concurrent_tasks=5,
    ),
    "design": AgentConfig(
        name="design",
        model=ModelConfig(
            name="gemini-2.5-flash",
            temperature=0.8,
        ),
        max_concurrent_tasks=5,
    ),
    "research": AgentConfig(
        name="research",
        model=ModelConfig(
            name="gemini-2.5-flash",
            temperature=0.5,
        ),
        max_concurrent_tasks=3,
    ),
}