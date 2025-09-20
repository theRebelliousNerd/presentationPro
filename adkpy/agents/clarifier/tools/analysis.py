"""Clarifier-specific analysis and summarization tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:  # pragma: no cover - allows unit tests without google-adk runtime
    from google.adk.tools.function_tool import FunctionTool
except ModuleNotFoundError:  # pragma: no cover
    class FunctionTool:  # type: ignore[duplicated-def]
        def __init__(self, func):
            self.func = func

QUESTION_KEYWORDS = {
    "audience": ["audience", "for", "presenting to"],
    "duration": ["minute", "slide", "hour", "long", "time"],
    "tone": ["tone", "style", "formal", "casual", "inspirational", "technical"],
    "key_points": ["include", "cover", "focus", "important", "should mention"],
    "constraints": ["constraint", "requirement", "must", "avoid"],
    "success": ["success", "outcome", "goal", "win"],
    "objective": ["objective", "goal", "purpose"],
    "call_to_action": ["call to action", "cta"],
    "layout": ["layout", "column", "sidebar", "arrangement"],
    "overlay": ["overlay", "ribbon", "card", "panel"],
    "background": ["background", "backdrop", "canvas", "wallpaper"],
    "pattern": ["pattern", "texture", "motif", "grid"],
}

STRUCTURED_FIELD_MAP = {
    "audience": ("audience",),
    "duration": ("length", "timeConstraintMin", "slideDensity"),
    "tone": ("tone",),
    "objective": ("objective",),
    "key_points": ("keyMessages", "mustInclude"),
    "success": ("successCriteria",),
    "call_to_action": ("callToAction",),
    "layout": ("designLayoutToken", "layoutPreference"),
    "overlay": ("designOverlayToken",),
    "background": ("designBackgroundToken",),
    "pattern": ("designPatternToken",),
}

_CRITICAL_FIELDS = ("audience", "objective")


def analyze_context(history: List[Dict[str, Any]], initial_input: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate how well we understand the user's goals based on provided context."""

    user_messages = [msg for msg in history if msg.get("role") == "user"]
    initial_text = (initial_input.get("text") or "").lower()

    signals = _seed_structured_signals(initial_input)
    signals = _augment_with_history(signals, user_messages)

    base_understanding = 0.30
    structured_count = sum(1 for present in signals.values() if present)
    base_understanding += 0.10 * min(structured_count, 4)

    if len(initial_text) > 100:
        base_understanding += 0.05

    total_understanding = min(1.0, base_understanding + len(user_messages) * 0.12)

    missing_fields = [field for field, present in signals.items() if not present]
    critical_missing = [field for field in _CRITICAL_FIELDS if field in missing_fields]
    needs_more_info = total_understanding < 0.7 or bool(critical_missing)

    return {
        "understanding_level": round(total_understanding, 2),
        "message_count": len(history),
        "missing_fields": missing_fields,
        "needs_more_info": needs_more_info,
        **{f"has_{field}": signals[field] for field in signals},
    }


def generate_question(context_analysis: Dict[str, Any], history: List[Dict[str, Any]]) -> str:
    """Choose the next clarifying question based on missing information."""

    asked = " ".join(_assistant_questions(history))
    missing_fields: List[str] = context_analysis.get("missing_fields", [])

    field_to_question = [
        ("audience", "Who is the target audience for this presentation? Please include their role or expertise level."),
        ("objective", "What is the primary objective or takeaway you want the audience to leave with?"),
        ("duration", "How long should the presentation run or how many slides should we aim for?"),
        ("key_points", "Are there specific topics or talking points that must be covered?"),
        ("tone", "What tone or style should the presentation use? (e.g., formal, conversational, inspirational, technical)"),
        ("layout", "Do you prefer a particular slide layout (single column, two column, sidebar, etc.)?"),
        ("overlay", "Should we include overlay elements such as ribbons, cards, or panels to highlight content?"),
        ("background", "Do you have a preferred background style (gradient, solid color, imagery)?"),
        ("pattern", "Would you like any pattern or texture in the background (e.g., grid, dots, subtle texture)?"),
        ("success", "What would success look like for this presentation? Any metrics or outcomes to hit?"),
        ("call_to_action", "Is there a particular call to action you want the audience to follow after the presentation?"),
    ]

    for field, question in field_to_question:
        if field in missing_fields and QUESTION_KEYWORDS.get(field) and not _already_asked(asked, QUESTION_KEYWORDS[field]):
            return question

    if not context_analysis.get("needs_more_info"):
        return (
            "Great, I have enough detail to proceed. I'll summarize the presentation goals next."
        )

    return (
        "Could you share any additional context or constraints that would help tailor this presentation (e.g., existing assets, must-include data points, brand considerations)?"
    )


def summarize_goals(history: List[Dict[str, Any]], initial_input: Dict[str, Any]) -> str:
    """Summarize the refined presentation goals gleaned from dialogue and form input."""

    requirements: Dict[str, Any] = {
        "topic": initial_input.get("text", "Not specified"),
        "audience": _coalesce(initial_input.get("audience")),
        "duration": _coalesce(initial_input.get("length")) or _format_duration(initial_input),
        "tone": _format_tone(initial_input.get("tone")),
        "key_points": _normalize_list(initial_input.get("keyMessages")) + _normalize_list(initial_input.get("mustInclude")),
        "constraints": _normalize_list(initial_input.get("constraints")) + _normalize_list(initial_input.get("mustAvoid")),
        "success_criteria": _normalize_list(initial_input.get("successCriteria")),
        "call_to_action": _coalesce(initial_input.get("callToAction")),
        "objective": _coalesce(initial_input.get("objective")),
        "layout": _coalesce(initial_input.get("designLayoutToken")),
        "overlay": _coalesce(initial_input.get("designOverlayToken")),
        "background": _coalesce(initial_input.get("designBackgroundToken")),
        "pattern": _coalesce(initial_input.get("designPatternToken")),
    }

    _fill_from_history(requirements, history)

    summary_sections = [f"**Presentation Topic**: {requirements['topic']}"]

    if requirements["objective"]:
        summary_sections.append(f"**Primary Objective**: {requirements['objective']}")
    if requirements["audience"]:
        summary_sections.append(f"**Target Audience**: {requirements['audience']}")
    if requirements["duration"]:
        summary_sections.append(f"**Duration/Length**: {requirements['duration']}")
    if requirements["tone"]:
        summary_sections.append(f"**Tone/Style**: {requirements['tone']}")
    if requirements["key_points"]:
        summary_sections.append("**Key Points to Cover**:\n" + "\n".join(f"- {point}" for point in requirements["key_points"]))
    if requirements["constraints"]:
        summary_sections.append("**Constraints & Must Haves**:\n" + "\n".join(f"- {item}" for item in requirements["constraints"]))
    if requirements["background"]:
        summary_sections.append(f"**Background Preference**: {requirements['background']}")
    if requirements["pattern"]:
        summary_sections.append(f"**Pattern Preference**: {requirements['pattern']}")
    if requirements["success_criteria"]:
        summary_sections.append("**Success Criteria**:\n" + "\n".join(f"- {criterion}" for criterion in requirements["success_criteria"]))
    if requirements["call_to_action"]:
        summary_sections.append(f"**Call to Action**: {requirements['call_to_action']}")

    summary_sections.append("\n**Next Steps**: I'll move ahead with the outline based on these requirements.")
    return "\n\n".join(summary_sections)


def _seed_structured_signals(initial_input: Dict[str, Any]) -> Dict[str, bool]:
    signals = {field: False for field in STRUCTURED_FIELD_MAP}
    for field, keys in STRUCTURED_FIELD_MAP.items():
        for key in keys:
            value = initial_input.get(key)
            if _has_value(value):
                signals[field] = True
                break
    return signals


def _augment_with_history(signals: Dict[str, bool], user_messages: List[Dict[str, Any]]) -> Dict[str, bool]:
    for msg in user_messages:
        content_raw = msg.get("content", "")
        content = content_raw.lower()
        for field, keywords in QUESTION_KEYWORDS.items():
            if field not in signals:
                continue
            if signals[field]:
                continue
            if any(keyword in content for keyword in keywords):
                signals[field] = True
    return signals


def _assistant_questions(history: List[Dict[str, Any]]) -> List[str]:
    return [msg.get("content", "").lower() for msg in history if msg.get("role") == "assistant"]


def _already_asked(asked_blob: str, keywords: List[str]) -> bool:
    return any(keyword in asked_blob for keyword in keywords)


def _fill_from_history(requirements: Dict[str, Any], history: List[Dict[str, Any]]) -> None:
    pending_field: Optional[str] = None

    for msg in history:
        role = msg.get("role")
        content_raw = msg.get("content", "")
        content = content_raw.lower()

        if role == "assistant":
            pending_field = _detect_field_from_content(content)
            continue

        if role != "user":
            continue

        if pending_field:
            _apply_field(requirements, pending_field, content_raw)
            pending_field = None

        if any(keyword in content for keyword in QUESTION_KEYWORDS["audience"]):
            requirements["audience"] = content_raw
        if any(keyword in content for keyword in QUESTION_KEYWORDS["duration"]):
            requirements["duration"] = content_raw
        if any(keyword in content for keyword in QUESTION_KEYWORDS["tone"]):
            requirements["tone"] = content_raw
        if any(keyword in content for keyword in QUESTION_KEYWORDS["key_points"]):
            requirements.setdefault("key_points", []).append(content_raw)
        if any(keyword in content for keyword in QUESTION_KEYWORDS["constraints"]):
            requirements.setdefault("constraints", []).append(content_raw)
        if any(keyword in content for keyword in QUESTION_KEYWORDS["background"]):
            requirements["background"] = content_raw
        if any(keyword in content for keyword in QUESTION_KEYWORDS["pattern"]):
            requirements["pattern"] = content_raw
        if any(keyword in content for keyword in QUESTION_KEYWORDS["success"]):
            requirements.setdefault("success_criteria", []).append(content_raw)
        if any(keyword in content for keyword in QUESTION_KEYWORDS["objective"]):
            requirements["objective"] = content_raw
        if any(keyword in content for keyword in QUESTION_KEYWORDS["call_to_action"]):
            requirements["call_to_action"] = content_raw

def _detect_field_from_content(content: str) -> Optional[str]:
    for field, keywords in QUESTION_KEYWORDS.items():
        if any(keyword in content for keyword in keywords):
            return field
    return None


def _apply_field(requirements: Dict[str, Any], field: str, value: str) -> None:
    if field == "key_points":
        requirements.setdefault("key_points", []).append(value)
    elif field == "constraints":
        requirements.setdefault("constraints", []).append(value)
    elif field == "success":
        requirements.setdefault("success_criteria", []).append(value)
    elif field == "call_to_action":
        requirements["call_to_action"] = value
    elif field == "duration":
        requirements["duration"] = value
    elif field in ("background", "pattern"):
        requirements[field] = value
    else:
        requirements[field] = value

def _coalesce(value: Any) -> Optional[str]:
    if not _has_value(value):
        return None
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value if _has_value(item)) or None
    if isinstance(value, dict):
        return ", ".join(f"{key}: {val}" for key, val in value.items() if _has_value(val)) or None
    return str(value)


def _normalize_list(value: Any) -> List[str]:
    if not _has_value(value):
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if _has_value(item)]
    return [str(value)]


def _format_duration(initial_input: Dict[str, Any]) -> Optional[str]:
    slide_density = initial_input.get("slideDensity")
    minutes = initial_input.get("timeConstraintMin")
    if slide_density and minutes:
        return f"Approximately {minutes} minutes with {slide_density} slide density"
    if minutes:
        return f"Approximately {minutes} minutes"
    if slide_density:
        return f"Preferred slide density: {slide_density}"
    return None


def _format_tone(tone: Any) -> Optional[str]:
    if isinstance(tone, dict):
        descriptors = []
        formality = tone.get("formality")
        energy = tone.get("energy")
        if formality is not None:
            descriptors.append(f"formality level {formality}")
        if energy is not None:
            descriptors.append(f"energy level {energy}")
        return ", ".join(descriptors) if descriptors else None
    return _coalesce(tone)


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set)):
        return any(_has_value(item) for item in value)
    if isinstance(value, dict):
        return any(_has_value(item) for item in value.values())
    return True


CLARIFIER_TOOLS = [
    FunctionTool(analyze_context),
    FunctionTool(generate_question),
    FunctionTool(summarize_goals),
]

__all__ = [
    "analyze_context",
    "generate_question",
    "summarize_goals",
    "CLARIFIER_TOOLS",
]
