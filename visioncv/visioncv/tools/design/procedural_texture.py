from __future__ import annotations

import base64
import io
from typing import Any, Dict, Sequence, Tuple

import numpy as np
from PIL import Image

def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    s = hex_color.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ValueError("Expected hex color in #RRGGBB format")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def _prepare_palette(colors: Sequence[str]) -> np.ndarray:
    if not colors:
        # Default to neutral greys
        colors = ("#0f172a", "#1e293b", "#475569", "#94a3b8")
    rgb = np.array([_hex_to_rgb(c) for c in colors], dtype=np.float32)
    return rgb


def _fractal_noise(height: int, width: int, scale: float, octaves: int, persistence: float, rng: np.random.Generator) -> np.ndarray:
    canvas = np.zeros((height, width), dtype=np.float32)
    frequency = 1.0
    amplitude = 1.0
    for _ in range(octaves):
        sample_h = max(1, int(round(height / (scale * frequency))))
        sample_w = max(1, int(round(width / (scale * frequency))))
        noise_small = rng.random((sample_h, sample_w), dtype=np.float32)
        noise = _resize(noise_small, (height, width))
        canvas += noise * amplitude
        frequency *= 2.0
        amplitude *= persistence
    # Normalize to 0..1
    canvas -= canvas.min()
    max_val = canvas.max()
    if max_val > 0:
        canvas /= max_val
    return canvas


def _cellular_noise(height: int, width: int, cell_count: int, rng: np.random.Generator) -> np.ndarray:
    pts = rng.random((cell_count, 2), dtype=np.float32)
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    coords = np.stack([(ys + 0.5) / float(height), (xs + 0.5) / float(width)], axis=-1)
    # Compute distance to closest feature point
    dists = np.min(np.linalg.norm(coords[:, :, None, :] - pts[None, None, :, :], axis=-1), axis=-1)
    dists -= dists.min()
    max_val = dists.max()
    if max_val > 0:
        dists /= max_val
    return 1.0 - dists


def _resize(arr: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    img = Image.fromarray((arr * 255).astype(np.uint8))
    resized = img.resize((size[1], size[0]), resample=Image.BICUBIC)
    return np.asarray(resized, dtype=np.float32) / 255.0


def _colorize(field: np.ndarray, palette: np.ndarray) -> np.ndarray:
    if palette.shape[0] == 1:
        rgb = palette[0][None, None, :]
        return np.repeat(np.repeat(rgb, field.shape[0], axis=0), field.shape[1], axis=1)
    positions = np.linspace(0.0, 1.0, palette.shape[0])
    flat = field.reshape(-1)
    mapped = np.empty((flat.shape[0], 3), dtype=np.float32)
    for channel in range(3):
        mapped[:, channel] = np.interp(flat, positions, palette[:, channel])
    rgb = mapped.reshape(field.shape[0], field.shape[1], 3)
    return np.clip(rgb, 0, 255)


def generate_procedural_texture(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a procedural texture and return it as a data URL."""

    width = int(input_obj.get("width") or 1024)
    height = int(input_obj.get("height") or 576)
    if width <= 0 or height <= 0 or width > 4096 or height > 4096:
        raise ValueError("Width/height must be between 1 and 4096")

    params = input_obj.get("parameters") or {}
    palette = _prepare_palette(params.get("color_palette_hex") or [])
    texture_type = (input_obj.get("texture_type") or "perlin_noise").lower()

    rng = np.random.default_rng(int(params.get("seed") or 0) or None)

    if texture_type == "cellular":
        cells = int(params.get("cell_count") or 24)
        field = _cellular_noise(height, width, max(4, cells), rng)
    else:
        scale = float(params.get("noise_scale") or 6.0)
        turbulence = float(params.get("turbulence") or 0.55)
        octaves = max(1, int(params.get("octaves") or 4))
        field = _fractal_noise(height, width, max(1.0, scale), octaves, max(0.05, min(turbulence, 0.95)), rng)

    rgb = _colorize(field, palette)
    img = Image.fromarray(rgb.astype(np.uint8))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return {"image_b64": b64, "imageDataUrl": f"data:image/png;base64,{b64}"}
