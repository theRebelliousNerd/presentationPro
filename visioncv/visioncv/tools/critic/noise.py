from typing import Any, Dict

import numpy as np

from ..util.images import decode_data_url, to_gray_luma, conv2d


def _gaussian_kernel(size: int = 5, sigma: float = 1.0) -> np.ndarray:
    ax = np.linspace(-(size // 2), size // 2, size)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2.0 * sigma**2))
    kernel /= kernel.sum()
    return kernel.astype(np.float32)


def measure_noise(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate image noise level via high-frequency energy.

    Method:
      - Gaussian blur to remove high-frequency components
      - Residual = original_gray - blurred
      - Noise metric = std(residual)
    """
    data_url = input_obj.get("screenshotDataUrl") or input_obj.get("imageDataUrl")
    if not data_url:
        raise ValueError("Missing 'screenshotDataUrl' or 'imageDataUrl'")
    img = decode_data_url(data_url)
    gray = to_gray_luma(img)
    gk = _gaussian_kernel(5, 1.0)
    blurred = conv2d(gray, gk)
    residual = gray - blurred
    noise_std = float(residual.std())
    # Normalize heuristic to 0..1 with soft saturation
    norm = min(1.0, noise_std / 50.0)
    return {"noise_std": round(noise_std, 2), "noise_level": round(norm, 3)}

