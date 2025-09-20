"""Design agent helper utilities built on shared design tokens."""

from __future__ import annotations

from typing import Any, Dict, Optional

try:  # pragma: no cover - allows local tests without google-adk
    from google.adk.tools.function_tool import FunctionTool
except ModuleNotFoundError:  # pragma: no cover - lightweight stub
    class FunctionTool:  # type: ignore[duplicated-def]
        def __init__(self, func):
            self.func = func

from adkpy.config.settings import load_design_tokens

_TOKENS = load_design_tokens()
_BACKGROUNDS = _TOKENS.get("backgrounds", {})
_PATTERNS = _TOKENS.get("patterns", {})

_THEME_DEFAULTS = {
    "brand": "brand-gradient-soft",
    "dark": "brand-gradient-contrast",
    "warm": "beige-paper",
}

_PATTERN_DEFAULTS = {
    "grid": "grid",
    "dots": "dots",
    "wave": "wave",
}


def build_background_code(theme: str, pattern: str) -> Dict[str, Any]:
    """Resolve background assets based on shared design tokens.

    Returns a JSON payload containing the chosen token identifiers plus
    resolved CSS/SVG strings so downstream renderers can both persist the
    semantic choice and immediately apply the styling.
    """

    background_token = _resolve_background_token(theme)
    pattern_token = _resolve_pattern_token(pattern)

    css = _BACKGROUNDS.get(background_token, {}).get("css")
    svg = _render_pattern(pattern_token) if pattern_token else None

    return {
        "tokens": {
            "background": background_token,
            "pattern": pattern_token,
        },
        "css": css,
        "svg": svg,
    }


def _resolve_background_token(theme: str) -> str:
    lowered = (theme or "").lower()
    if lowered in _BACKGROUNDS:
        return lowered
    if lowered in _THEME_DEFAULTS:
        candidate = _THEME_DEFAULTS[lowered]
        if candidate in _BACKGROUNDS:
            return candidate
    # Fallback to first background token for safety.
    return next(iter(_BACKGROUNDS.keys()), "brand-gradient-soft")


def _resolve_pattern_token(pattern: str) -> Optional[str]:
    lowered = (pattern or "").lower()
    if lowered in _PATTERNS:
        return lowered
    if lowered in _PATTERN_DEFAULTS:
        candidate = _PATTERN_DEFAULTS[lowered]
        if candidate in _PATTERNS:
            return candidate
    return None


def _render_pattern(token: str) -> Optional[str]:
    if not token:
        return None
    pattern = _PATTERNS.get(token)
    if not pattern:
        return None

    generator = pattern.get("generator")
    if generator == "dots":
        return _render_dots(pattern)
    return pattern.get("svg")


def _render_dots(pattern: Dict[str, Any]) -> str:
    base_svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='1280' height='720'>"
        "<g fill='rgba(255,255,255,0.06)'>" + _generate_dot_grid() + "</g></svg>"
    )
    template = pattern.get("svg")
    # If the token supplies a template, prefer it for future customisation.
    if template and "${DOTS}" in template:
        return template.replace("${DOTS}", _generate_dot_grid())
    if template:
        return template
    return base_svg


def _generate_dot_grid() -> str:
    circles = []
    for y in range(40, 720, 80):
        offset = 20 if (y // 80) % 2 else 0
        for x in range(40, 1280, 80):
            cx = x + offset
            circles.append(f"<circle cx='{cx}' cy='{y}' r='3'/>")
    return "".join(circles)


DESIGN_TOOLS = [FunctionTool(build_background_code)]

__all__ = ["build_background_code", "DESIGN_TOOLS"]
