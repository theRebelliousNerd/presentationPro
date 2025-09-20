"""Configuration helpers for agent capability metadata."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml

CONFIG_DIR = Path(__file__).parent
CAPABILITIES_PATH = CONFIG_DIR / "agent_capabilities.yaml"
DESIGN_TOKENS_PATH = CONFIG_DIR / "design_tokens.json"


@lru_cache(maxsize=1)
def load_capabilities() -> Dict[str, Any]:
    """Load the agent capability manifest."""

    with CAPABILITIES_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@lru_cache(maxsize=1)
def load_design_tokens() -> Dict[str, Any]:
    """Load the shared design token catalog."""

    with DESIGN_TOKENS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


__all__ = [
    "CONFIG_DIR",
    "CAPABILITIES_PATH",
    "DESIGN_TOKENS_PATH",
    "load_capabilities",
    "load_design_tokens",
]
