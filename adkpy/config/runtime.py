"""Runtime configuration helpers."""

from __future__ import annotations

import os
from typing import Dict

from .settings import load_capabilities


def get_agent_endpoints() -> Dict[str, str]:
    """Return a map of agent name -> base URL derived from env vars and manifest."""

    capabilities = load_capabilities()
    agents = capabilities.get("agents", {})
    endpoints: Dict[str, str] = {}

    for agent_name, metadata in agents.items():
        env_var = metadata.get("url_env")
        default_host = metadata.get("service")
        port = metadata.get("port")
        if not env_var:
            continue
        value = os.environ.get(env_var)
        if value:
            endpoints[agent_name] = value
        elif default_host and port:
            endpoints[agent_name] = f"http://{default_host}:{port}"
    return endpoints


__all__ = ["get_agent_endpoints"]
