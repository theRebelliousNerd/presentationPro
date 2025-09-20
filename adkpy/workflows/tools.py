
"""Workflow-level helper utilities for PresentationPro."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:  # pragma: no cover - allow unit tests to stub dependencies
    from tools.arango_graph_rag_tool import (
        ArangoGraphRAGTool,
        Asset,
        RetrieveResponse,
    )
except ImportError:  # pragma: no cover
    try:
        from adkpy.tools.arango_graph_rag_tool import (
            ArangoGraphRAGTool,
            Asset,
            RetrieveResponse,
        )
    except ImportError:  # pragma: no cover
        ArangoGraphRAGTool = None  # type: ignore
        Asset = None  # type: ignore
        RetrieveResponse = None  # type: ignore

try:  # pragma: no cover - lazy optional dependency for Gemini image generation
    from agents.design_image_agent import (
        DesignImageAgent,
        ImageGenerateInput,
        save_image_to_file,
    )
except ImportError:  # pragma: no cover
    try:
        from adkpy.agents.design_image_agent import (
            DesignImageAgent,
            ImageGenerateInput,
            save_image_to_file,
        )
    except ImportError:  # pragma: no cover
        DesignImageAgent = None  # type: ignore
        ImageGenerateInput = None  # type: ignore
        save_image_to_file = None  # type: ignore

try:  # pragma: no cover - prefer package-relative import when available
    from config.settings import load_design_tokens
except ImportError:  # pragma: no cover
    from adkpy.config.settings import load_design_tokens

_RAG_TOOL: Optional[ArangoGraphRAGTool] = None  # type: ignore[assignment]
_IMAGE_AGENT: Optional[DesignImageAgent] = None  # type: ignore[assignment]
GENERATED_IMAGES_DIR = Path(__file__).resolve().parents[1] / "app" / "generated_images"
_TOKENS = load_design_tokens()
_THEME_INDEX = {
    "brand": ("brand-gradient-soft", "grid", "beige-ribbon", "two-column"),
    "modern": ("brand-gradient-contrast", "grid", "glass-panel", "sidebar"),
    "warm": ("beige-paper", "dots", "beige-ribbon", "single-column"),
    "dark": ("brand-gradient-contrast", "wave", "slate-card", "two-column"),
}


def _ensure_rag_tool() -> Optional[ArangoGraphRAGTool]:  # type: ignore[valid-type]
    global _RAG_TOOL
    if ArangoGraphRAGTool is None:
        return None
    if _RAG_TOOL is None:
        _RAG_TOOL = ArangoGraphRAGTool()
    return _RAG_TOOL


def _ensure_image_agent() -> Optional[DesignImageAgent]:  # type: ignore[valid-type]
    global _IMAGE_AGENT
    if DesignImageAgent is None:
        return None
    if _IMAGE_AGENT is None:
        _IMAGE_AGENT = DesignImageAgent()
    return _IMAGE_AGENT


def rag_ingest_workflow_tool(presentation_id: str, assets: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Ingest uploaded assets into the Graph RAG store."""

    assets = list(assets or [])
    if not assets or ArangoGraphRAGTool is None or Asset is None:
        return {"ok": True, "docs": 0, "chunks": 0}

    tool = _ensure_rag_tool()
    if tool is None:
        return {"ok": True, "docs": 0, "chunks": 0}

    typed_assets: List[Asset] = []  # type: ignore[type-arg]
    for asset in assets:
        if not asset:
            continue
        name = asset.get("name") or asset.get("filename") or "asset"
        typed_assets.append(
            Asset(
                presentationId=presentation_id,
                name=name,
                url=asset.get("url"),
                text=asset.get("text"),
                kind=asset.get("kind"),
            )
        )
    response = tool.ingest(typed_assets)
    if hasattr(response, "model_dump"):
        return response.model_dump()
    return dict(response or {})


def rag_retrieve_workflow_tool(presentation_id: str, query: str, limit: int = 6) -> Dict[str, Any]:
    """Retrieve supporting context for an outline section using Graph RAG."""

    if not query or ArangoGraphRAGTool is None:
        return {"chunks": []}

    tool = _ensure_rag_tool()
    if tool is None:
        return {"chunks": []}

    response = tool.retrieve(presentation_id, query, limit=limit)
    if RetrieveResponse is not None and isinstance(response, RetrieveResponse):
        return response.model_dump()
    if hasattr(response, "model_dump"):
        return response.model_dump()
    return dict(response or {})


def finalize_payload(*, slides: Iterable[Any], script: Optional[str], ragContext: Any) -> Dict[str, Any]:
    """Build the final payload returned to the frontend."""

    normalized_slides: List[Dict[str, Any]] = []
    for slide in slides or []:
        if hasattr(slide, "model_dump"):
            normalized_slides.append(slide.model_dump(by_alias=True))
        else:
            normalized_slides.append(dict(slide))
    payload = {
        "slides": normalized_slides,
        "script": script,
        "ragContext": ragContext,
    }
    return payload


def evaluate_quality(*, slides: Iterable[Any], ragContext: Any) -> Dict[str, Any]:
    """Placeholder quality evaluator used by legacy loops (critic now handles QA)."""

    return {"should_continue": False, "telemetry": {}}


def map_theme_to_design(initialInput: Dict[str, Any], slide: Dict[str, Any]) -> Dict[str, str]:
    """Derive design token ids (background/pattern/overlay/layout) for a slide."""

    style = (initialInput.get("graphicStyle") or initialInput.get("template") or "brand").lower()
    background, pattern, overlay, layout = _THEME_INDEX.get(style, _THEME_INDEX["brand"])

    preferred_bg = initialInput.get("designBackgroundToken")
    preferred_pattern = initialInput.get("designPatternToken")
    preferred_overlay = initialInput.get("designOverlayToken")
    preferred_layout = initialInput.get("designLayoutToken")

    background_token = preferred_bg if _is_valid_background(preferred_bg) else background
    pattern_token = preferred_pattern if _is_valid_pattern(preferred_pattern) else pattern
    overlay_token = preferred_overlay if _is_valid_overlay(preferred_overlay) else overlay
    layout_token = preferred_layout if _is_valid_layout(preferred_layout) else layout

    slide_meta = (slide.get("metadata") or {}) if isinstance(slide, dict) else {}
    slide_bg = slide_meta.get("designBackgroundToken") or slide_meta.get("backgroundToken")
    slide_pattern = slide_meta.get("designPatternToken") or slide_meta.get("patternToken")
    slide_overlay = slide_meta.get("designOverlayToken") or slide_meta.get("overlayToken")
    slide_layout = slide_meta.get("designLayoutToken") or slide_meta.get("layoutToken")

    if _is_valid_background(slide_bg):
        background_token = slide_bg
    if _is_valid_pattern(slide_pattern):
        pattern_token = slide_pattern
    if _is_valid_overlay(slide_overlay):
        overlay_token = slide_overlay
    if _is_valid_layout(slide_layout):
        layout_token = slide_layout

    return {
        "background": background_token,
        "pattern": pattern_token,
        "overlay": overlay_token,
        "layout": layout_token,
    }


def prepare_design_payload(
    slideId: str,
    designResponse: Optional[Dict[str, Any]],
    tokens: Dict[str, str],
    presentationId: Optional[str] = None,
) -> Dict[str, Any]:
    """Wrap the design agent response so workflow mutations can attach it to the slide."""

    payload: Dict[str, Any] = {"tokens": tokens}
    if isinstance(designResponse, dict):
        payload.update({k: v for k, v in designResponse.items() if v is not None})
    if "layers" not in payload:
        layers: List[Dict[str, Any]] = []
        bg_token = tokens.get("background")
        if bg_token and bg_token in _TOKENS.get("backgrounds", {}):
            layers.append({
                "kind": "background",
                "token": bg_token,
                "css": _TOKENS["backgrounds"][bg_token].get("css"),
            })
        overlay_token = tokens.get("overlay")
        if overlay_token and overlay_token in _TOKENS.get("overlays", {}):
            layers.append({
                "kind": "overlay",
                "token": overlay_token,
                "css": _TOKENS["overlays"][overlay_token].get("css"),
            })
        layout_token = tokens.get("layout")
        if layout_token and layout_token in _TOKENS.get("layouts", {}):
            layout_data = _TOKENS["layouts"][layout_token]
            layers.append({
                "kind": "layout",
                "token": layout_token,
                "columns": layout_data.get("columns"),
                "gutter": layout_data.get("gutter"),
                "weights": layout_data.get("weights"),
            })
        payload["layers"] = layers

    prompt = None
    if isinstance(designResponse, dict):
        prompt = designResponse.get("prompt") or designResponse.get("imagePrompt")
        payload.setdefault("type", designResponse.get("type"))
    if payload.get("type") == "image" and prompt:
        image = generate_background_image(prompt, tokens, presentationId)
        if image:
            payload["image"] = image
            payload["type"] = "image"
    return {"design": {slideId: payload}}


def generate_background_image(
    prompt: Optional[str], tokens: Dict[str, str], presentation_id: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Generate a background image using Gemini Flash when enabled."""

    if not prompt or ImageGenerateInput is None or save_image_to_file is None:
        return None
    agent = _ensure_image_agent()
    if agent is None:
        return None

    request = ImageGenerateInput(
        title="",
        content=[],
        prompt=prompt,
        theme=tokens.get("background", "brand"),
        pattern="gradient",
        presentationId=presentation_id,
    )
    try:
        image = agent.generate_overlay(request)
    except Exception:
        return None

    try:
        os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)
        fpath = save_image_to_file(image, str(GENERATED_IMAGES_DIR))
        url = f"/generated-images/{Path(fpath).name}"
        return {"prompt": prompt, "url": url, "path": fpath}
    except Exception:
        return None


def prepare_critic_payload(slideId: str, critique: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Wrap critic output into the structure expected by merge_critic_feedback."""

    if not isinstance(critique, dict):
        return {"slides": []}
    slide_payload = dict(critique)
    slide_payload.setdefault("id", slideId)
    return {"slides": [slide_payload]}


def prepare_notes_payload(slideId: str, polisherResult: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Wrap notes polisher output into the structure expected by merge_notes."""

    note = None
    if isinstance(polisherResult, dict):
        note = polisherResult.get("rephrasedSpeakerNotes") or polisherResult.get("speakerNotes")
    if not note:
        return {"notes": {}}
    return {"notes": {slideId: note}}


def select_notes_tone(initialInput: Dict[str, Any]) -> Dict[str, str]:
    """Derive a friendly tone label for the notes polisher agent."""

    tone = initialInput.get("notesTone") or initialInput.get("tone")
    if isinstance(tone, dict):
        for key in ("style", "label", "descriptor", "name"):
            value = tone.get(key)
            if isinstance(value, str) and value.strip():
                return {"tone": value.strip()}
        if "formality" in tone and "energy" in tone:
            return {"tone": f"formality {tone['formality']} / energy {tone['energy']}"}
    if isinstance(tone, str) and tone.strip():
        return {"tone": tone.strip()}
    return {"tone": "professional"}


def load_slides_from_input(slides: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Utility to normalise slide payloads provided directly in workflow inputs."""

    normalised = []
    for slide in slides or []:
        normalised.append(dict(slide))
    return {"slides": normalised}


def prepare_research_summary(state: Any) -> Dict[str, Any]:
    """Return research findings and context in a lightweight payload."""

    findings = []
    if hasattr(state, "research"):
        findings = getattr(state.research, "findings", []) or []
    elif isinstance(state, dict):
        findings = state.get("research", {}).get("findings", [])
    return {"research": {"findings": findings}}


def collect_regression_metrics(state: Any) -> Dict[str, Any]:
    """Collect coarse-grained metrics for regression/validation workflows."""

    slides = getattr(state, "slides", []) or []
    total_bullets = sum(len(getattr(slide, "content", [])) for slide in slides)
    tokens = sum(len((getattr(slide, "design", {}) or {}).get("tokens", {})) for slide in slides)
    normalized_slides = []
    for slide in slides:
        if hasattr(slide, "model_dump"):
            normalized_slides.append(slide.model_dump(by_alias=True))
        elif hasattr(slide, "__dict__"):
            normalized_slides.append(vars(slide).copy())
        else:
            normalized_slides.append(dict(slide))
    return {
        "metrics": {
            "slideCount": len(slides),
            "totalBullets": total_bullets,
            "avgBulletsPerSlide": total_bullets / len(slides) if slides else 0,
            "designTokenCount": tokens,
            "hasScript": bool(getattr(state, "script", None)),
        },
        "slides": normalized_slides,
        "script": getattr(state, "script", None),
    }


def _is_valid_background(token: Any) -> bool:
    return isinstance(token, str) and token in _TOKENS.get("backgrounds", {})


def _is_valid_pattern(token: Any) -> bool:
    return isinstance(token, str) and token in _TOKENS.get("patterns", {})


def _is_valid_overlay(token: Any) -> bool:
    return isinstance(token, str) and token in _TOKENS.get("overlays", {})


def _is_valid_layout(token: Any) -> bool:
    return isinstance(token, str) and token in _TOKENS.get("layouts", {})


WORKFLOW_TOOLS = {
    "graph_rag.ingest": rag_ingest_workflow_tool,
    "graph_rag.retrieve": rag_retrieve_workflow_tool,
    "workflow.finalize_payload": finalize_payload,
    "workflow.evaluate_quality": evaluate_quality,
    "workflow.map_design_tokens": map_theme_to_design,
    "workflow.prepare_design_payload": prepare_design_payload,
    "workflow.prepare_critic_payload": prepare_critic_payload,
    "workflow.prepare_notes_payload": prepare_notes_payload,
    "workflow.select_notes_tone": select_notes_tone,
    "workflow.load_slides": load_slides_from_input,
    "workflow.collect_regression_metrics": collect_regression_metrics,
    "workflow.prepare_research_summary": prepare_research_summary,
}


__all__ = [
    "rag_ingest_workflow_tool",
    "rag_retrieve_workflow_tool",
    "finalize_payload",
    "evaluate_quality",
    "map_theme_to_design",
    "prepare_design_payload",
    "prepare_critic_payload",
    "prepare_notes_payload",
    "select_notes_tone",
    "load_slides_from_input",
    "prepare_research_summary",
    "collect_regression_metrics",
    "WORKFLOW_TOOLS",
]
