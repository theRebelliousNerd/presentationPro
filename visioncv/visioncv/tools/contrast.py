import base64
import io
from typing import Any, Dict

from PIL import Image
import numpy as np


def _decode_data_url_png_or_jpeg(data_url: str) -> Image.Image:
    if not isinstance(data_url, str) or ";base64," not in data_url:
        raise ValueError("Expected data URL with base64 content")
    header, b64 = data_url.split(",", 1)
    raw = base64.b64decode(b64)
    return Image.open(io.BytesIO(raw)).convert("RGB")


def color_contrast(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Simple image statistics as a placeholder for contrast/visibility.

    Returns mean brightness, variance, and a crude darken recommendation.
    """
    data_url = input_obj.get("screenshotDataUrl")
    img = _decode_data_url_png_or_jpeg(data_url)
    arr = np.asarray(img).astype(np.float32)
    # convert to luma approximation
    luma = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    mean = float(luma.mean())
    var = float(luma.var())
    # heuristics
    recommend_darken = bool(mean > 170 and var < 800)
    overlay = 0.25 if recommend_darken else 0.0
    return {
        "mean": round(mean, 2),
        "variance": round(var, 2),
        "recommendDarken": recommend_darken,
        "overlay": overlay,
    }

