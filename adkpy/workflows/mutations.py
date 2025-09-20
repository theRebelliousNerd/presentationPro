"""State mutation helpers for PresentationPro workflows."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

try:
    from schemas.workflow_state import (
        PresentationWorkflowState,
        RagChunk,
        SectionRagContext,
        OutlineSection,
        SlideState,
        QualityMetrics,
        WorkflowQualityState,
    )
except ImportError:  # repo context
    from adkpy.schemas.workflow_state import (
        PresentationWorkflowState,
        RagChunk,
        SectionRagContext,
        OutlineSection,
        SlideState,
        QualityMetrics,
        WorkflowQualityState,
    )


def _normalize_chunks(section_id: str, title: str, chunks: Iterable[Dict[str, Any]]) -> SectionRagContext:
    normalized_chunks = [RagChunk(**chunk) for chunk in chunks]
    return SectionRagContext(sectionId=section_id, title=title, chunks=normalized_chunks)


def cache_ingest_summary(state: PresentationWorkflowState, result: Dict[str, Any], *, inputs: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None) -> PresentationWorkflowState:
    state.ingest_summary = result or {}
    return state


def store_clarify_result(state: PresentationWorkflowState, result: Dict[str, Any], *, inputs: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None) -> PresentationWorkflowState:
    response_text = result.get("refinedGoals") or result.get("response") or ""
    state.clarify.response = response_text
    state.clarify.finished = bool(result.get("finished"))
    if telemetry := result.get("telemetry"):
        state.clarify.telemetry = telemetry
    if session_id := result.get("session_id") or result.get("sessionId"):
        state.metadata["sessionId"] = session_id
    if inputs:
        state.presentation_id = inputs.get("presentationId", state.presentation_id)
        if history := inputs.get("history"):
            state.history = history
    if rag_chunks := result.get("ragChunks"):
        state.rag.presentation = [RagChunk(**chunk) for chunk in rag_chunks]
    return state


def store_outline_result(state: PresentationWorkflowState, result: Dict[str, Any], *, inputs: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None) -> PresentationWorkflowState:
    sections_payload = result.get("outline") or []
    sections: List[OutlineSection] = []
    for idx, item in enumerate(sections_payload):
        if isinstance(item, dict):
            title = item.get("title") or item.get("heading") or f"Section {idx + 1}"
            bullets = item.get("bullets") or item.get("points") or []
        else:
            title = str(item)
            bullets = []
        sections.append(
            OutlineSection(
                title=title,
                bullets=bullets,
            )
        )
    state.outline.sections = sections
    state.outline.raw = result
    return state


def cache_section_rag(
    state: PresentationWorkflowState,
    result: Dict[str, Any],
    *,
    inputs: Optional[Dict[str, Any]] = None,
    item: Optional[Dict[str, Any]] = None,
) -> PresentationWorkflowState:
    if not item:
        return state
    if isinstance(item, dict):
        section_id = item.get("id") or item.get("title") or "section"
        title = item.get("title") or section_id
    else:
        section_id = getattr(item, "id", None) or getattr(item, "title", None) or "section"
        title = getattr(item, "title", None) or section_id
    chunks = result.get("chunks") or []
    context = _normalize_chunks(section_id, title, chunks)
    state.rag.sections[section_id] = context
    state.rag.sections[title] = context
    return state


def upsert_slide(
    state: PresentationWorkflowState,
    result: Dict[str, Any],
    *,
    inputs: Optional[Dict[str, Any]] = None,
    item: Optional[Dict[str, Any]] = None,
) -> PresentationWorkflowState:
    slide_payload = result.get("slide") or result
    slide_id = slide_payload.get("id") or (item.get("id") if isinstance(item, dict) else getattr(item, "id", None))
    existing = next((slide for slide in state.slides if slide.id == slide_id), None)
    if existing:
        existing.title = slide_payload.get("title", existing.title)
        existing.content = slide_payload.get("content", existing.content)
        existing.speakerNotes = slide_payload.get("speakerNotes", existing.speakerNotes)
        existing.citations = slide_payload.get("citations", existing.citations)
        existing.metadata.update(slide_payload.get("metadata", {}))
    else:
        new_slide = SlideState(
            id=slide_id or SlideState().id,
            title=slide_payload.get("title", "Untitled slide"),
            content=slide_payload.get("content", []),
            speakerNotes=slide_payload.get("speakerNotes"),
            citations=slide_payload.get("citations", []),
            metadata=slide_payload.get("metadata", {}),
        )
        state.slides.append(new_slide)
    return state


def merge_critic_feedback(
    state: PresentationWorkflowState,
    result: Dict[str, Any],
    *,
    inputs: Optional[Dict[str, Any]] = None,
    item: Optional[Dict[str, Any]] = None,
) -> PresentationWorkflowState:
    revised_slides = result.get("slides") or []
    if not revised_slides:
        return state
    indexed = {slide.id: slide for slide in state.slides}
    for payload in revised_slides:
        slide_id = payload.get("id") or ((item or {}).get("id") if isinstance(item, dict) else None)
        if slide_id in indexed:
            indexed[slide_id].content = payload.get("content", indexed[slide_id].content)
            indexed[slide_id].speakerNotes = payload.get("speakerNotes", indexed[slide_id].speakerNotes)
            if citations := payload.get("citations"):
                indexed[slide_id].citations = citations
    return state


def merge_notes(state: PresentationWorkflowState, result: Dict[str, Any], *, inputs: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None) -> PresentationWorkflowState:
    notes_map = result.get("notes") or {}
    indexed = {slide.id: slide for slide in state.slides}
    for slide_id, notes in notes_map.items():
        if slide_id in indexed:
            indexed[slide_id].speakerNotes = notes
    return state


def merge_design(state: PresentationWorkflowState, result: Dict[str, Any], *, inputs: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None) -> PresentationWorkflowState:
    design_data = result.get("design") or {}
    indexed = {slide.id: slide for slide in state.slides}
    for slide_id, payload in design_data.items():
        if slide_id in indexed:
            indexed[slide_id].design.update(payload)
    return state


def store_script(state: PresentationWorkflowState, result: Dict[str, Any], *, inputs: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None) -> PresentationWorkflowState:
    state.script = result.get("script") or state.script
    return state


def update_research_cache(state: PresentationWorkflowState, result: Dict[str, Any], *, inputs: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None) -> PresentationWorkflowState:
    if chunks := result.get("chunks"):
        state.rag.presentation = [RagChunk(**chunk) for chunk in chunks]
    return state


def append_research_findings(state: PresentationWorkflowState, result: Dict[str, Any], *, inputs: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None) -> PresentationWorkflowState:
    findings = result.get("findings") or result.get("insights") or []
    if findings:
        state.research.findings.extend(findings)
    return state


def set_slides(state: PresentationWorkflowState, result: Dict[str, Any], *, inputs: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None) -> PresentationWorkflowState:
    """Replace the slide collection with the payload returned by the slide-writer."""

    slides_payload = result.get("slides") or []
    slides: List[SlideState] = []
    for payload in slides_payload:
        slide = SlideState(
            id=payload.get("id") or SlideState().id,
            title=payload.get("title", "Untitled slide"),
            content=payload.get("content") or [],
            speakerNotes=payload.get("speakerNotes"),
            citations=payload.get("citations") or [],
            metadata=payload.get("metadata") or {},
        )
        slides.append(slide)
    state.slides = slides
    return state



def store_quality_snapshot(state: PresentationWorkflowState, result: Dict[str, Any], *, inputs: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None) -> PresentationWorkflowState:
    quality_log = state.metadata.setdefault("quality", [])
    quality_log.append({
        "missingCitations": result.get("missingCitations", []),
        "violations": result.get("violations", []),
        "telemetry": result.get("telemetry", {}),
    })
    return state


def store_completion_payload(state: PresentationWorkflowState, result: Dict[str, Any], *, inputs: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None) -> PresentationWorkflowState:
    """Store presentation completion payload and script in workflow state."""

    presentation = result.get("presentation") or {}
    if presentation:
        slides_map = presentation.get("slides") or {}
        slides: List[SlideState] = []
        for key, payload in slides_map.items():
            slide = SlideState(
                id=str(key),
                title=payload.get("title", f"Slide {key}"),
                content=payload.get("content") or payload.get("bullets") or [],
                speakerNotes=payload.get("speakerNotes"),
                citations=payload.get("citations") or [],
                metadata=payload.get("metadata") or {},
            )
            slides.append(slide)
        if slides:
            state.slides = slides
        if script := presentation.get("script"):
            state.script = script
        state.final_response = presentation
    if session_id := result.get("session_id"):
        state.metadata.setdefault("sessionId", session_id)
    return state


def set_final_response(state: PresentationWorkflowState, result: Dict[str, Any], *, inputs: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None) -> PresentationWorkflowState:
    if result.get("script"):
        state.script = result.get("script")
    state.final_response = result
    return state


# Quality Gate Mutations

def update_quality_metrics(
    state: PresentationWorkflowState,
    result: Dict[str, Any],
    *,
    inputs: Optional[Dict[str, Any]] = None,
    item: Optional[Dict[str, Any]] = None
) -> PresentationWorkflowState:
    """Update quality metrics tracking for a slide."""
    slide_id = result.get("slideId")
    if not slide_id:
        return state

    # Update workflow-level quality state
    state.quality_state.total_slides_assessed += 1

    if result.get("requires_fixes"):
        state.quality_state.slides_requiring_fixes += 1

    if result.get("requires_manual_review"):
        state.quality_state.manual_review_required = True

    if not result.get("passes_quality_gate"):
        quality_level = result.get("quality_level", "unknown")
        state.quality_state.quality_gate_failures.append(
            f"Slide {slide_id}: {quality_level} quality"
        )

    # Find and update the specific slide
    for slide in state.slides:
        if slide.id == slide_id:
            # Create quality metrics from result
            quality_metrics = QualityMetrics(
                overall_score=result.get("overall_score", 100),
                issues_found=result.get("issues", []),
                requires_manual_review=result.get("requires_manual_review", False),
                quality_level=result.get("quality_level", "excellent")
            )
            slide.quality_metrics = quality_metrics
            break

    return state


def merge_enhanced_critic_feedback(
    state: PresentationWorkflowState,
    result: Dict[str, Any],
    *,
    inputs: Optional[Dict[str, Any]] = None,
    item: Optional[Dict[str, Any]] = None
) -> PresentationWorkflowState:
    """Merge enhanced critic feedback with quality metrics."""
    enhanced_critics = result.get("enhanced_critics", {})

    for slide_id, feedback in enhanced_critics.items():
        # Find the slide to update
        for slide in state.slides:
            if slide.id == slide_id:
                # Update slide with critique results
                critique = feedback.get("critique", {})
                if critique:
                    slide.title = critique.get("title", slide.title)
                    slide.content = critique.get("content", slide.content)
                    slide.speakerNotes = critique.get("speakerNotes", slide.speakerNotes)
                    if image_prompt := critique.get("imagePrompt"):
                        slide.image_prompt = image_prompt

                # Update quality metrics
                quality_data = feedback.get("quality_metrics", {})
                applied_fixes = feedback.get("applied_fixes", [])

                if quality_data:
                    # Update existing quality metrics with final assessment
                    slide.quality_metrics.overall_score = quality_data.get("final_score", slide.quality_metrics.overall_score)
                    slide.quality_metrics.fixes_applied = applied_fixes
                    slide.quality_metrics.quality_level = quality_data.get("quality_level", slide.quality_metrics.quality_level)

                    # Track improvements at workflow level
                    improvement = quality_data.get("improvement", 0)
                    if improvement > 0:
                        state.quality_state.quality_improvements.append(
                            f"Slide {slide_id}: +{improvement} points"
                        )

                # Count applied fixes
                if applied_fixes:
                    state.quality_state.auto_fixes_applied += len(applied_fixes)

                break

    return state


def store_quality_summary(
    state: PresentationWorkflowState,
    result: Dict[str, Any],
    *,
    inputs: Optional[Dict[str, Any]] = None,
    item: Optional[Dict[str, Any]] = None
) -> PresentationWorkflowState:
    """Store comprehensive quality assessment summary."""
    summary = result.get("summary", "")
    overall_quality = result.get("overall_quality", "unknown")
    statistics = result.get("statistics", {})

    # Update workflow quality state with final statistics
    state.quality_state.overall_presentation_score = int(statistics.get("average_score", 100))

    # Update compliance levels based on statistics
    avg_score = statistics.get("average_score", 100)
    if avg_score >= 90:
        compliance_level = "excellent"
    elif avg_score >= 75:
        compliance_level = "good"
    elif avg_score >= 60:
        compliance_level = "acceptable"
    else:
        compliance_level = "poor"

    state.quality_state.brand_compliance_level = compliance_level
    state.quality_state.accessibility_compliance_level = compliance_level
    state.quality_state.visual_clarity_level = compliance_level

    # Store summary in metadata
    state.metadata["quality_summary"] = {
        "summary": summary,
        "overall_quality": overall_quality,
        "statistics": statistics
    }

    return state


def _get_quality_level_from_score(score: int) -> str:
    """Helper to determine quality level from score."""
    if score >= 90:
        return "excellent"
    elif score >= 75:
        return "good"
    elif score >= 60:
        return "acceptable"
    else:
        return "poor"


__all__ = [
    "cache_ingest_summary",
    "store_clarify_result",
    "store_outline_result",
    "cache_section_rag",
    "upsert_slide",
    "merge_critic_feedback",
    "merge_notes",
    "merge_design",
    "store_script",
    "update_research_cache",
    "append_research_findings",
    "set_slides",
    "store_completion_payload",
    "store_quality_snapshot",
    "set_final_response",
    # Quality Gate Mutations
    "update_quality_metrics",
    "merge_enhanced_critic_feedback",
    "store_quality_summary",
]
