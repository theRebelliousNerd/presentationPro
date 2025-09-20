"""Critic agent helper utilities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from google.adk.tools.function_tool import FunctionTool


def compile_asset_snippets(assets: Optional[List[Dict[str, Any]]], max_chars: int = 400) -> str:
    """Return short asset snippets for fact checking and citations."""

    if not assets:
        return ""
    snippets = []
    for asset in assets:
        text = (asset.get("text") or "")[:max_chars]
        snippets.append(f"- {asset.get('name', 'Asset')}: {text}")
    return "\n".join(snippets)


CRITIC_TOOLS = [FunctionTool(compile_asset_snippets)]

__all__ = ["compile_asset_snippets", "CRITIC_TOOLS"]
