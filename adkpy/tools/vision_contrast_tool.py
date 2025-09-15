"""
VisionContrastTool

Analyze slide screenshot (PNG) to estimate brightness/variance and recommend overlay darkening to improve text legibility.
"""

from __future__ import annotations

import base64
from typing import Optional
from pydantic import BaseModel

from app.llm import analyze_screenshot_contrast


class VisionAnalyzeInput(BaseModel):
  screenshotDataUrl: str


class VisionAnalyzeOutput(BaseModel):
  mean: float
  variance: float
  recommendDarken: bool
  overlay: float


class VisionContrastTool:
  def analyze(self, data: VisionAnalyzeInput) -> VisionAnalyzeOutput:
    # decode data URL
    try:
      _, b64 = data.screenshotDataUrl.split(",", 1)
    except ValueError:
      b64 = data.screenshotDataUrl
    png_bytes = base64.b64decode(b64)
    stats = analyze_screenshot_contrast(png_bytes) or {"mean": 128.0, "variance": 500.0}
    mean = float(stats.get("mean", 128.0))
    var = float(stats.get("variance", 500.0))
    recommend = (mean > 150.0) or (var > 2000.0)
    overlay = 0.0
    if recommend:
      overlay = min(0.45, 0.15 + (mean - 100.0) / 300.0 + (var / 10000.0))
    return VisionAnalyzeOutput(mean=mean, variance=var, recommendDarken=recommend, overlay=round(overlay, 2))
