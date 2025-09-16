"""
Design Image Subagent

Generates presentation-friendly overlay graphics (PNG, 1280x720) using a
combination of heuristics, optional LLM guidance, and procedural drawing.

Primary goals:
- Clarity over complexity (inspired by Dan Roam's "Back of the Napkin")
- Brand/muted/dark themes with gradient bases and subtle shapes
- Optional contrast-aware darkening based on screenshot analysis

If Gemini image generation is added later, this agent can route prompts to that
API and fall back to procedural generation when needed.
"""

from __future__ import annotations

import io
import os
import uuid
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

from PIL import Image, ImageDraw

from pydantic import BaseModel, Field
import base64

try:
    # Optional: use the vision contrast tool if available
    from tools.vision_contrast_tool import VisionContrastTool
except Exception:
    VisionContrastTool = None  # type: ignore


IMAGE_W = 1280
IMAGE_H = 720


class ImageGenerateInput(BaseModel):
    title: str = ""
    content: List[str] = Field(default_factory=list)
    speakerNotes: Optional[str] = None
    theme: str = "brand"  # brand | muted | dark
    pattern: str = "gradient"  # gradient | shapes | grid | dots | wave
    prompt: Optional[str] = None
    baseImage: Optional[str] = None  # data URL screenshot for contrast analysis
    imageModel: Optional[str] = None
    presentationId: Optional[str] = None


class ImageEditInput(BaseModel):
    instruction: str
    baseImage: str  # data URL of base image to edit
    presentationId: Optional[str] = None


@dataclass
class Palette:
    bg_a: Tuple[int, int, int]
    bg_b: Tuple[int, int, int]
    accent: Tuple[int, int, int]
    accent2: Tuple[int, int, int]


THEME_PALETTES: Dict[str, Palette] = {
    "brand": Palette(
        bg_a=(25, 41, 64),  # Deep Navy
        bg_b=(85, 98, 115), # Slate Blue
        accent=(115, 191, 80),  # Action Green
        accent2=(255, 255, 255),
    ),
    "muted": Palette(
        bg_a=(60, 70, 80),
        bg_b=(90, 100, 110),
        accent=(210, 210, 210),
        accent2=(240, 240, 240),
    ),
    "dark": Palette(
        bg_a=(18, 20, 24),
        bg_b=(34, 40, 46),
        accent=(90, 110, 130),
        accent2=(210, 210, 210),
    ),
}


def lerp(a: Tuple[int, int, int], b: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def draw_gradient(img: Image.Image, p: Palette) -> None:
    # simple diagonal gradient
    draw = ImageDraw.Draw(img)
    steps = 200
    for i in range(steps):
        t = i / (steps - 1)
        color = lerp(p.bg_a, p.bg_b, t)
        # draw wide diagonal bands
        y = int((t) * IMAGE_H)
        draw.rectangle([(0, y), (IMAGE_W, y + 6)], fill=color)


def draw_shapes(img: Image.Image, p: Palette, scale: float = 1.0) -> None:
    d = ImageDraw.Draw(img, "RGBA")
    # subtle circles and rounded rects
    a1 = int(25 * max(0.0, min(scale, 1.0)))
    a2 = int(20 * max(0.0, min(scale, 1.0)))
    d.ellipse([(IMAGE_W*0.1, IMAGE_H*0.1), (IMAGE_W*0.35, IMAGE_H*0.45)], fill=(*p.accent, a1))
    d.rounded_rectangle([(IMAGE_W*0.65, IMAGE_H*0.55), (IMAGE_W*0.95, IMAGE_H*0.95)], radius=28, fill=(*p.accent2, a2))


def draw_grid(img: Image.Image, p: Palette, scale: float = 1.0) -> None:
    d = ImageDraw.Draw(img, "RGBA")
    step = 40
    stroke = (*p.accent2, int(20 * max(0.0, min(scale, 1.0))))
    for x in range(0, IMAGE_W, step):
        d.line([(x, 0), (x, IMAGE_H)], fill=stroke, width=1)
    for y in range(0, IMAGE_H, step):
        d.line([(0, y), (IMAGE_W, y)], fill=stroke, width=1)


def draw_dots(img: Image.Image, p: Palette, scale: float = 1.0) -> None:
    d = ImageDraw.Draw(img, "RGBA")
    import random
    random.seed(42)
    count = int(120 * max(0.2, min(scale, 1.0)))
    for _ in range(count):
        x = int(random.random() * IMAGE_W)
        y = int(random.random() * IMAGE_H)
        r = int(2 + random.random() * 4)
        d.ellipse([(x-r, y-r), (x+r, y+r)], fill=(*p.accent2, int(20 * max(0.0, min(scale, 1.0)))))


def draw_wave(img: Image.Image, p: Palette, scale: float = 1.0) -> None:
    d = ImageDraw.Draw(img, "RGBA")
    # draw a few translucent wave bands from bottom
    band_h = IMAGE_H // 6
    bands = 3
    for i in range(bands):
        alpha = int((20 + i * 10) * max(0.0, min(scale, 1.0)))
        y0 = IMAGE_H - (i+1) * band_h
        d.rounded_rectangle([(0, y0), (IMAGE_W, IMAGE_H)], radius=40, fill=(*p.accent2, alpha))


class DesignImageAgent:
    def __init__(self) -> None:
        self.vision = VisionContrastTool() if VisionContrastTool else None
        # Optional Gemini image generation
        self.enable_gemini = os.getenv("ENABLE_GEMINI_IMAGE", "false").lower() == "true"
        self._gemini_init()

    def _gemini_init(self) -> None:
        self.gemini = None
        if not self.enable_gemini:
            return
        try:
            import google.generativeai as genai  # type: ignore
            api_key = os.environ.get("GOOGLE_GENAI_API_KEY")
            if not api_key:
                return
            genai.configure(api_key=api_key)
            # Model name may evolve; allow override via env, else default preview
            model_name = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview")
            self.gemini = genai.GenerativeModel(model_name=model_name)
        except Exception:
            self.gemini = None

    def generate_overlay(self, req: ImageGenerateInput) -> Image.Image:
        # Try Gemini image if enabled and prompt is present
        if self.gemini and req.prompt:
            try:
                img = self._try_gemini_generate(req)
                if img is not None:
                    return img
            except Exception:
                pass

        palette = THEME_PALETTES.get(req.theme, THEME_PALETTES["brand"])
        img = Image.new("RGB", (IMAGE_W, IMAGE_H), color=palette.bg_a)
        draw_gradient(img, palette)

        # Load design rule for theme/pattern to modulate intensity
        intensity_scale = 1.0
        try:
            from app.design_rules import get_design_rule
            rule = get_design_rule(req.theme, req.pattern)
            if rule and isinstance(rule.get("intensity"), dict):
                pattern_intensity = float(rule["intensity"].get("pattern", 1.0))
                intensity_scale = max(0.1, min(pattern_intensity, 1.0))
        except Exception:
            pass

        pattern = req.pattern or "gradient"
        if pattern == "shapes":
            draw_shapes(img, palette, intensity_scale)
        elif pattern == "grid":
            draw_grid(img, palette, intensity_scale)
        elif pattern == "dots":
            draw_dots(img, palette, intensity_scale)
        elif pattern == "wave":
            draw_wave(img, palette, intensity_scale)
        else:
            # gradient-only already applied
            pass

        # Optional contrast-aware darken based on screenshot
        try:
            if self.vision and req.baseImage and req.baseImage.startswith("data:image"):
                # simple parse of data URL
                header, b64 = req.baseImage.split(",", 1)
                import base64
                png_bytes = base64.b64decode(b64)
                vis = self.vision.analyze_from_png_bytes(png_bytes)  # type: ignore[attr-defined]
                # heuristic: apply overlay up to 0.35
                overlay = min(max(float(vis.overlay or 0), 0.0), 0.35) if hasattr(vis, 'overlay') else 0.0
                if overlay > 0:
                    dark = Image.new("RGBA", (IMAGE_W, IMAGE_H), color=(0, 0, 0, int(overlay * 255)))
                    img = img.convert("RGBA")
                    img.alpha_composite(dark)
                    img = img.convert("RGB")
        except Exception:
            pass

        return img

    def _try_gemini_generate(self, req: ImageGenerateInput) -> Optional[Image.Image]:
        if not self.gemini:
            return None
        # This is a best-effort attempt. Some SDK versions return image data
        # as inline_data parts; others may not support direct image bytes.
        prompt = self._compose_prompt(req)
        try:
            resp = self.gemini.generate_content([prompt])  # type: ignore
            # Attempt to find inline image data
            parts = []
            try:
                for cand in getattr(resp, "candidates", []) or []:
                    content = getattr(cand, "content", None)
                    for part in getattr(content, "parts", []) or []:
                        parts.append(part)
            except Exception:
                pass
            for part in parts:
                data = getattr(part, "inline_data", None)
                if data and getattr(data, "mime_type", "").startswith("image"):
                    b64 = getattr(data, "data", None)
                    if b64:
                        raw = base64.b64decode(b64)
                        buf = io.BytesIO(raw)
                        im = Image.open(buf).convert("RGB")
                        return im.resize((IMAGE_W, IMAGE_H))
        except Exception:
            return None
        return None

    def _compose_prompt(self, req: ImageGenerateInput) -> str:
        # A concise prompt for overlay backgrounds
        theme = req.theme
        pattern = req.pattern
        title = (req.title or "").strip()
        bullets = " | ".join([(c or "").strip() for c in (req.content or [])])
        return (
            "Create a clean presentation slide overlay background (1280x720).\n"
            f"Theme: {theme}. Pattern: {pattern}.\n"
            "Requirements: minimalist shapes, high legibility, subtle gradients, no text, no logos, no faces.\n"
            f"Slide title: {title}\n"
            f"Bullets: {bullets}\n"
            "Output: one PNG image."
        )

    def edit_overlay(self, req: ImageEditInput) -> Image.Image:
        # Very light-touch editing: apply subtle adjustments based on instruction keywords
        # and re-run contrast-aware overlay if possible
        base = decode_data_url_to_image(req.baseImage)
        d = ImageDraw.Draw(base, "RGBA")
        text = (req.instruction or "").lower()
        if "darker" in text:
            d.rectangle([(0, 0), (IMAGE_W, IMAGE_H)], fill=(0, 0, 0, 35))
        if "lighter" in text:
            d.rectangle([(0, 0), (IMAGE_W, IMAGE_H)], fill=(255, 255, 255, 20))
        if "grid" in text:
            draw_grid(base, THEME_PALETTES["brand"])  # use brand grid as accent
        return base


def decode_data_url_to_image(data_url: str) -> Image.Image:
    assert data_url.startswith("data:image")
    header, b64 = data_url.split(",", 1)
    import base64
    raw = base64.b64decode(b64)
    buf = io.BytesIO(raw)
    return Image.open(buf).convert("RGBA").resize((IMAGE_W, IMAGE_H))


def save_image_to_file(img: Image.Image, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    fname = f"{uuid.uuid4().hex}.png"
    fpath = os.path.join(out_dir, fname)
    img.save(fpath, format="PNG", optimize=True)
    return fpath
