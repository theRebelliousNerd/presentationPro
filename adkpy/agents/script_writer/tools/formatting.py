"""Script writer helper functions."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from google.adk.tools.function_tool import FunctionTool

try:
    from adkpy.tools.shared import format_assets as shared_format_assets
    from adkpy.tools.shared import format_slides as shared_format_slides
except ModuleNotFoundError:  # pragma: no cover - fallback inside agent-only container
    # Local fallback implementations mirror adkpy.tools.shared without requiring the package.
    def shared_format_slides(slides: List[Dict[str, Any]]) -> str:
        blocks: List[str] = []
        for index, slide in enumerate(slides, start=1):
            lines = [f"## Slide {index}"]
            lines.append(f"Title: {slide.get('title', 'N/A')}")
            bullets = "\n".join(f"- {bullet}" for bullet in (slide.get('content') or []))
            if bullets:
                lines.append("Content:")
                lines.append(bullets)
            lines.append(f"Speaker Notes: {slide.get('speakerNotes', 'N/A')}")
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)

    def shared_format_assets(assets: Optional[List[Dict[str, Any]]]) -> str:
        if not assets:
            return ""
        return "\n".join(
            f"- {asset.get('name', 'N/A')} - {asset.get('url', 'N/A')}" for asset in assets
        )


def format_slides(slides: List[Dict[str, Any]]) -> str:
    """Format slide dictionaries into a readable text block for scripting."""

    return shared_format_slides(slides)


def format_assets(assets: Optional[List[Dict[str, Any]]]) -> str:
    """Format asset metadata into a bullet list for bibliography references."""

    return shared_format_assets(assets)


SCRIPT_WRITER_TOOLS = [
    FunctionTool(format_slides),
    FunctionTool(format_assets),
]

__all__ = ["format_slides", "format_assets", "SCRIPT_WRITER_TOOLS"]
