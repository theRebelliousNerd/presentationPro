import base64
import io
from typing import Tuple

import numpy as np
from PIL import Image


def decode_data_url(data_url: str) -> Image.Image:
    if not isinstance(data_url, str):
        raise ValueError("Expected base64 string or data URL")
    if ";base64," in data_url:
        _, b64 = data_url.split(",", 1)
    else:
        b64 = data_url
    raw = base64.b64decode(b64)
    return Image.open(io.BytesIO(raw)).convert("RGB")


def to_gray_luma(img: Image.Image) -> np.ndarray:
    arr = np.asarray(img).astype(np.float32)
    luma = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    return luma


def conv2d(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Naive valid convolution with zero padding at borders."""
    kh, kw = kernel.shape
    pad_h, pad_w = kh // 2, kw // 2
    padded = np.pad(img, ((pad_h, pad_h), (pad_w, pad_w)), mode="edge")
    out = np.zeros_like(img, dtype=np.float32)
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            window = padded[i:i+kh, j:j+kw]
            out[i, j] = float(np.sum(window * kernel))
    return out


def downsample(arr: np.ndarray, max_wh: Tuple[int, int] = (96, 96)) -> np.ndarray:
    h, w = arr.shape[:2]
    max_w, max_h = max_wh
    scale = max(1, int(max(h / max_h, w / max_w)))
    if scale <= 1:
        return arr
    new_h, new_w = h // scale, w // scale
    # simple average pooling
    arr = arr[:new_h*scale, :new_w*scale]
    arr = arr.reshape(new_h, scale, new_w, scale).mean(axis=(1, 3))
    return arr
