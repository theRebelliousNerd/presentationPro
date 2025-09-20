"""Research agent helper utilities."""

from __future__ import annotations

from typing import Dict, List, Optional

from google.adk.tools.function_tool import FunctionTool

try:
    from google.adk.tools import WebSearchTool
except Exception:  # Tool may be absent in some environments
    WebSearchTool = None  # type: ignore


def get_web_evidence(query: str, top_k: int = 5, allow_domains: Optional[List[str]] = None) -> str:
    """Retrieve search snippets suitable for grounding the model."""

    if not WebSearchTool:
        return ""

    tool = WebSearchTool(allow_domains=allow_domains)
    results = tool.search(query, top_k=top_k)
    return "\n".join(
        f"- {r.title}\n  Snippet: {r.snippet}\n  Source: {r.url}"
        for r in results
    )


RESEARCH_TOOLS = [FunctionTool(get_web_evidence)]

__all__ = ["get_web_evidence", "RESEARCH_TOOLS"]
