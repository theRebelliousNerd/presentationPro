"""Configuration exports for PresentationPro."""

from .settings import CONFIG_DIR, CAPABILITIES_PATH, load_capabilities
from .runtime import get_agent_endpoints

__all__ = [
    "CONFIG_DIR",
    "CAPABILITIES_PATH",
    "load_capabilities",
    "get_agent_endpoints",
]
