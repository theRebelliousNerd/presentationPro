"""
TelemetryTool

Collect and emit standardized usage telemetry for every agent/tool step.

This is an in-memory implementation with optional line-delimited JSON file sink.
"""

from __future__ import annotations

import json
import os
import time
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
  step: str
  agent: Optional[str] = None
  model: Optional[str] = None
  promptTokens: int = 0
  completionTokens: int = 0
  durationMs: int = 0
  cost: Optional[float] = None
  at: float = Field(default_factory=lambda: time.time())
  meta: Dict[str, Any] = Field(default_factory=dict)


class TelemetryTool:
  def __init__(self, sink_path: Optional[str] = None) -> None:
    # default sink under repo if provided
    self._buffer: List[TelemetryEvent] = []
    self._sink = sink_path or os.environ.get("ADK_TELEMETRY_SINK")

  def record(self, event: TelemetryEvent) -> None:
    self._buffer.append(event)
    if self._sink:
      try:
        os.makedirs(os.path.dirname(self._sink), exist_ok=True)
        with open(self._sink, "a", encoding="utf-8") as f:
          f.write(json.dumps(event.model_dump()) + "\n")
      except Exception:
        # non-fatal sink errors
        pass

  def attach_usage(self, usage: Dict[str, Any], *, step: str, agent: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> TelemetryEvent:
    evt = TelemetryEvent(
      step=step,
      agent=agent,
      model=usage.get("model"),
      promptTokens=int(usage.get("promptTokens") or 0),
      completionTokens=int(usage.get("completionTokens") or 0),
      durationMs=int(usage.get("durationMs") or 0),
      meta=meta or {},
    )
    self.record(evt)
    return evt

  def aggregate(self) -> Dict[str, Any]:
    total = {
      "events": len(self._buffer),
      "promptTokens": 0,
      "completionTokens": 0,
      "durationMs": 0,
    }
    by_agent: Dict[str, Dict[str, Any]] = {}
    for e in self._buffer:
      total["promptTokens"] += e.promptTokens
      total["completionTokens"] += e.completionTokens
      total["durationMs"] += e.durationMs
      if e.agent:
        agg = by_agent.setdefault(e.agent, {"promptTokens": 0, "completionTokens": 0, "durationMs": 0, "events": 0})
        agg["events"] += 1
        agg["promptTokens"] += e.promptTokens
        agg["completionTokens"] += e.completionTokens
        agg["durationMs"] += e.durationMs
    return {"total": total, "byAgent": by_agent}

  def flush(self) -> None:
    self._buffer.clear()

