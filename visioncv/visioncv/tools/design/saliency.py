"""ARCHIVED: Basic saliency map using gradient magnitude (Sobel filters).

This tool has been superseded by saliency_spectral.py which provides superior
frequency-domain saliency detection using the Hou & Zhang spectral residual method.

Kept for backward compatibility only. New implementations should use:
  - design.saliency_spectral for all saliency detection needs

Original implementation: Simple edge-detection based saliency
Replacement: Advanced spectral saliency with better focal point detection
Archived: 2025-09-20
"""

from typing import Any, Dict, List

import numpy as np

from ..util.images import decode_data_url, to_gray_luma, conv2d, downsample


def saliency_map(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """[DEPRECATED] Produce a simple saliency heatmap via gradient magnitude.

    NOTICE: This function is deprecated. Use saliency_spectral() instead for better results.
    This basic gradient-based approach is retained only for backward compatibility.

    The spectral saliency method (saliency_spectral.py) provides:
    - Better detection of salient regions
    - More accurate focal point identification
    - Improved performance on complex images
    - Frequency-domain analysis vs simple edge detection

    Output is a small 2D heatmap (list[list[float]] in 0..1) for lightweight transport.
    """
    # Log deprecation warning if available
    import warnings
    warnings.warn(
        "saliency_map is deprecated. Use saliency_spectral for better results.",
        DeprecationWarning,
        stacklevel=2
    )

    data_url = input_obj.get("screenshotDataUrl") or input_obj.get("imageDataUrl")
    if not data_url:
        raise ValueError("Missing 'screenshotDataUrl' or 'imageDataUrl'")
    img = decode_data_url(data_url)
    gray = to_gray_luma(img)
    # Sobel filters (basic edge detection approach)
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    ky = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
    gx = conv2d(gray, kx)
    gy = conv2d(gray, ky)
    mag = np.sqrt(gx * gx + gy * gy)
    small = downsample(mag, (64, 36))
    # normalize 0..1
    if small.max() > 0:
        norm = (small - small.min()) / (small.max() - small.min() + 1e-6)
    else:
        norm = small * 0.0
    heatmap: List[List[float]] = norm.astype(np.float32).tolist()
    return {"heatmap": heatmap}

