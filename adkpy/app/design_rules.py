"""
Design rules seeding and retrieval for overlay generation.

Stores presentation design heuristics in ArangoDB so image/design agents can
retrieve context about patterns, palettes, and stylistic guidance.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from .db import get_db


DEFAULT_RULES = [
    {
        "_key": "brand:gradient",
        "theme": "brand",
        "pattern": "gradient",
        "guidelines": [
            "Favor diagonal gradients to suggest motion without distraction.",
            "Keep background contrast moderate; prioritize text legibility.",
            "Use Action Green sparingly to call attention to key areas.",
        ],
        "intensity": {"pattern": 0.4, "shapes": 0.0},
    },
    {
        "_key": "brand:shapes",
        "theme": "brand",
        "pattern": "shapes",
        "guidelines": [
            "Use a few large translucent shapes (circles/rounded rects).",
            "Avoid intersecting shapes behind text areas.",
            "Keep accent density under 20% of the slide area.",
        ],
        "intensity": {"pattern": 0.6, "shapes": 0.4},
    },
    {
        "_key": "brand:grid",
        "theme": "brand",
        "pattern": "grid",
        "guidelines": [
            "Light grids support diagrams (Dan Roam's clarity).",
            "Use thin strokes with high translucency.",
            "Leave margins clean around title area.",
        ],
        "intensity": {"pattern": 0.3},
    },
    {
        "_key": "brand:dots",
        "theme": "brand",
        "pattern": "dots",
        "guidelines": [
            "Scatter dots randomly with low opacity.",
            "Avoid dot clusters behind body text.",
        ],
        "intensity": {"pattern": 0.25},
    },
    {
        "_key": "brand:wave",
        "theme": "brand",
        "pattern": "wave",
        "guidelines": [
            "Use 2–3 wave bands from bottom for balance.",
            "Keep opacity below 12% to preserve legibility.",
        ],
        "intensity": {"pattern": 0.2},
    },
    {
        "_key": "muted:gradient",
        "theme": "muted",
        "pattern": "gradient",
        "guidelines": ["Softer gradients; rely more on typography contrast."],
        "intensity": {"pattern": 0.35},
    },
    {
        "_key": "dark:gradient",
        "theme": "dark",
        "pattern": "gradient",
        "guidelines": ["Prefer darker base; ensure sufficient text contrast."],
        "intensity": {"pattern": 0.45},
    },
]


def ensure_design_rules() -> None:
    db = get_db()
    col_name = "design_rules"
    if not db.has_collection(col_name):
        db.create_collection(col_name)
    col = db.collection(col_name)
    # Seed if empty
    if col.count() == 0:
        for rule in DEFAULT_RULES:
            try:
                col.insert(rule)
            except Exception:
                pass


def get_design_rule(theme: str, pattern: str) -> Optional[Dict[str, Any]]:
    try:
        db = get_db()
        col = db.collection("design_rules")
        key = f"{theme}:{pattern}"
        if col.has(key):
            return col.get(key)
        # fallback to theme:gradient
        fallback_key = f"{theme}:gradient"
        return col.get(fallback_key) if col.has(fallback_key) else None
    except Exception:
        return None

