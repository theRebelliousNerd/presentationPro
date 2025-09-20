"""Shared workflow state models for PresentationPro."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


class RagChunk(BaseModel):
    chunk_key: Optional[str] = Field(default=None, alias="chunkKey")
    name: str
    text: str
    url: Optional[str] = None
    score: float = 0.0


class SectionRagContext(BaseModel):
    section_id: str = Field(alias="sectionId")
    title: str
    chunks: List[RagChunk] = Field(default_factory=list)


class PresentationRagState(BaseModel):
    presentation: List[RagChunk] = Field(default_factory=list)
    sections: Dict[str, SectionRagContext] = Field(default_factory=dict)


class ClarifyState(BaseModel):
    response: Optional[str] = None
    finished: bool = False
    telemetry: Dict[str, Any] = Field(default_factory=dict)


class OutlineSection(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    description: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)


class OutlineState(BaseModel):
    sections: List[OutlineSection] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


class QualityMetrics(BaseModel):
    """Quality assessment metrics for slides."""
    overall_score: int = Field(default=100, description="Overall quality score (0-100)")
    accessibility_score: int = Field(default=100, description="WCAG accessibility score")
    brand_score: int = Field(default=100, description="Brand consistency score")
    clarity_score: int = Field(default=100, description="Visual clarity score")
    issues_found: List[str] = Field(default_factory=list)
    fixes_applied: List[str] = Field(default_factory=list)
    requires_manual_review: bool = Field(default=False)
    assessment_timestamp: Optional[str] = None
    quality_level: str = Field(default="excellent")  # excellent, good, acceptable, poor


class SlideState(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    content: List[str] = Field(default_factory=list)
    speakerNotes: Optional[str] = None
    citations: List[str] = Field(default_factory=list)
    design: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    quality_metrics: QualityMetrics = Field(default_factory=QualityMetrics)
    image_url: Optional[str] = None
    image_prompt: Optional[str] = None


class ResearchState(BaseModel):
    prompt: Optional[str] = None
    query: Optional[str] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowQualityState(BaseModel):
    """Quality tracking for the entire workflow."""
    overall_presentation_score: int = Field(default=100)
    total_slides_assessed: int = Field(default=0)
    slides_requiring_fixes: int = Field(default=0)
    auto_fixes_applied: int = Field(default=0)
    manual_review_required: bool = Field(default=False)
    quality_gate_failures: List[str] = Field(default_factory=list)
    quality_improvements: List[str] = Field(default_factory=list)
    brand_compliance_level: str = Field(default="excellent")
    accessibility_compliance_level: str = Field(default="excellent")
    visual_clarity_level: str = Field(default="excellent")


class PresentationWorkflowState(BaseModel):
    presentation_id: Optional[str] = Field(default=None, alias="presentationId")
    audience: Optional[str] = None
    tone: Optional[str] = None
    length: Optional[str] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)
    rag: PresentationRagState = Field(default_factory=PresentationRagState)
    clarify: ClarifyState = Field(default_factory=ClarifyState)
    outline: OutlineState = Field(default_factory=OutlineState)
    slides: List[SlideState] = Field(default_factory=list)
    script: Optional[str] = None
    research: ResearchState = Field(default_factory=ResearchState)
    ingest_summary: Dict[str, Any] = Field(default_factory=dict)
    final_response: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    quality_state: WorkflowQualityState = Field(default_factory=WorkflowQualityState)

    model_config = ConfigDict(populate_by_name=True)



__all__ = [
    "RagChunk",
    "SectionRagContext",
    "PresentationRagState",
    "ClarifyState",
    "OutlineSection",
    "OutlineState",
    "QualityMetrics",
    "SlideState",
    "ResearchState",
    "WorkflowQualityState",
    "PresentationWorkflowState",
]

