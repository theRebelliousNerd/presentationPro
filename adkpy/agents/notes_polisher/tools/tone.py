"""Notes polisher helper utilities."""

from __future__ import annotations

from typing import Dict

from google.adk.tools.function_tool import FunctionTool

TONE_GUIDANCE: Dict[str, str] = {
    "professional": "Use formal, confident language with polished phrasing.",
    "concise": "Keep sentences short, remove filler, and focus on essentials.",
    "engaging": "Adopt energetic language, invite participation, and use vivid verbs.",
    "casual": "Use conversational phrasing and approachable language to keep it friendly.",
}


def tone_guidelines(tone: str) -> str:
    """Return coaching guidance for the requested tone."""

    return TONE_GUIDANCE.get(tone.lower(), "Adopt a clear, audience-friendly tone.")


NOTES_POLISHER_TOOLS = [FunctionTool(tone_guidelines)]

__all__ = ["tone_guidelines", "NOTES_POLISHER_TOOLS"]
