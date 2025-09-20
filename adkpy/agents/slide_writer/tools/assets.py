"""Slide writer helper utilities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from google.adk.tools.function_tool import FunctionTool


def summarize_assets(assets: Optional[List[Dict[str, Any]]], max_chars: int = 800) -> str:
    """Produce a concise asset summary for grounding slide content."""

    if not assets:
        return ""
    summaries = []
    for asset in assets:
        text = (asset.get("text") or "")[:max_chars]
        summaries.append(f"- {asset.get('name', 'Asset')}: {text}")
    return "\n".join(summaries)


SLIDE_WRITER_TOOLS = [FunctionTool(summarize_assets)]

__all__ = ["summarize_assets", "SLIDE_WRITER_TOOLS"]
