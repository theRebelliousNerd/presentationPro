"""
A2A Messages

Pydantic models for agent-to-agent message envelopes and common content types.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class Telemetry(BaseModel):
  step: str
  agent: Optional[str] = None
  model: Optional[str] = None
  promptTokens: int = 0
  completionTokens: int = 0
  durationMs: int = 0
  cost: Optional[float] = None
  at: float


class ClarificationQuestion(BaseModel):
  question: str


class ClarificationAnswer(BaseModel):
  answer: str


class ClarificationSummary(BaseModel):
  refinedGoals: str
  constraints: Optional[Dict[str, Any]] = None


class OutlineProposal(BaseModel):
  outline: List[str]


class OutlineRevisionRequest(BaseModel):
  operations: List[str]


class SlideDraft(BaseModel):
  title: str
  content: List[str]
  speakerNotes: str
  imagePrompt: str
  citations: Optional[List[str]] = None


class Critique(BaseModel):
  issues: List[str]
  suggestions: List[str]
  diffs: Optional[str] = None


class RevisionRequest(BaseModel):
  instructions: str


class SlideFinal(SlideDraft):
  pass


class DesignRequest(BaseModel):
  slide: Dict[str, Any]
  theme: Literal["brand", "muted", "dark"] = "brand"
  pattern: Literal["gradient", "shapes", "grid", "dots", "wave"] = "gradient"
  screenshot: Optional[str] = None


class DesignBackground(BaseModel):
  type: Literal["code", "prompt"]
  code: Optional[Dict[str, Optional[str]]] = None
  prompt: Optional[str] = None


MessageContent = Union[
  ClarificationQuestion,
  ClarificationAnswer,
  ClarificationSummary,
  OutlineProposal,
  OutlineRevisionRequest,
  SlideDraft,
  Critique,
  RevisionRequest,
  SlideFinal,
  DesignRequest,
  DesignBackground,
]


class Attachment(BaseModel):
  name: str
  url: Optional[str] = None


class Message(BaseModel):
  traceId: str
  conversationId: str
  fromAgent: str
  toAgent: str
  type: str
  content: MessageContent
  attachments: Optional[List[Attachment]] = None
  createdAt: float = Field(default_factory=lambda: __import__("time").time())
  telemetry: Optional[Telemetry] = None


def make_message(trace_id: str, conv_id: str, from_agent: str, to_agent: str, mtype: str, content: MessageContent, *, attachments: Optional[List[Attachment]] = None, telemetry: Optional[Telemetry] = None) -> Message:
  return Message(
    traceId=trace_id,
    conversationId=conv_id,
    fromAgent=from_agent,
    toAgent=to_agent,
    type=mtype,
    content=content,
    attachments=attachments,
    telemetry=telemetry,
  )

