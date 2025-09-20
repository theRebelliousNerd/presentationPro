"""Shared utility helpers for presentation agents."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def format_slides(slides: List[Dict[str, Any]]) -> str:
    """Convert a list of slide dictionaries into a readable text block."""

    blocks: List[str] = []
    for index, slide in enumerate(slides, start=1):
        lines = [f"## Slide {index}"]
        lines.append(f"Title: {slide.get('title', 'N/A')}")
        bullets = "\n".join(f"- {bullet}" for bullet in (slide.get("content") or []))
        if bullets:
            lines.append("Content:")
            lines.append(bullets)
        lines.append(f"Speaker Notes: {slide.get('speakerNotes', 'N/A')}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def format_assets(assets: Optional[List[Dict[str, Any]]]) -> str:
    """Render asset metadata into a bullet list."""

    if not assets:
        return ""
    return "\n".join(
        f"- {asset.get('name', 'N/A')} - {asset.get('url', 'N/A')}"
        for asset in assets
    )


__all__ = ["format_slides", "format_assets"]
