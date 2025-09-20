"""Utility helpers for the outline agent."""

from __future__ import annotations

import json
import re
from typing import List


def parse_outline(text: str, max_items: int = 12) -> List[str]:
    """Parse model output into a list of slide titles."""

    cleaned_text = text.strip().removeprefix("`json").removesuffix("`")
    try:
        parsed_json = json.loads(cleaned_text)
        if isinstance(parsed_json, list) and all(isinstance(item, str) for item in parsed_json):
            return parsed_json[:max_items]
        raise ValueError("Parsed JSON is not a list of strings.")
    except (json.JSONDecodeError, ValueError):
        lines = text.split("\n")
        outline: List[str] = []
        pattern = re.compile(r"^\s*[\d\-\*\.]+\s*")
        for line in lines:
            cleaned_line = pattern.sub("", line).strip()
            if cleaned_line:
                outline.append(cleaned_line)
        return outline[:max_items]


__all__ = ["parse_outline"]
