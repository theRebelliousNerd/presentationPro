from typing import Any, Dict, List

import numpy as np

from ..util.images import decode_data_url, to_gray_luma, conv2d, downsample


def _avg_kernel(k: int) -> np.ndarray:
    k = max(3, int(k) | 1)  # odd
    ker = np.ones((k, k), dtype=np.float32)
    ker /= ker.size
    return ker


def _gaussian_kernel(size: int = 7, sigma: float = 2.0) -> np.ndarray:
    ax = np.linspace(-(size // 2), size // 2, size)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2.0 * sigma**2))
    kernel /= kernel.sum()
    return kernel.astype(np.float32)


def saliency_spectral(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Spectral Residual Saliency (Hou & Zhang) with simple smoothing.

    Returns a normalized heatmap (2D list of floats 0..1) optionally downsampled for transport.
    Inputs:
      - screenshotDataUrl or imageDataUrl
      - output_size: [w,h] optional downsample size for output heatmap
    """
    data_url = input_obj.get("screenshotDataUrl") or input_obj.get("imageDataUrl")
    if not data_url:
        raise ValueError("Missing 'screenshotDataUrl' or 'imageDataUrl'")
    img = decode_data_url(data_url)
    gray = to_gray_luma(img)
    # normalize to [0,1]
    gmin, gmax = float(gray.min()), float(gray.max())
    if gmax > gmin:
        gray_n = (gray - gmin) / (gmax - gmin)
    else:
        gray_n = gray * 0.0

    F = np.fft.fft2(gray_n)
    log_amp = np.log(np.abs(F) + 1e-8)
    phase = np.angle(F)
    avg = conv2d(log_amp, _avg_kernel(9))
    spectral_residual = log_amp - avg
    F_sr = np.exp(spectral_residual + 1j * phase)
    sal = np.abs(np.fft.ifft2(F_sr))**2
    sal = conv2d(sal, _gaussian_kernel(9, 2.0))
    # normalize 0..1
    smin, smax = float(sal.min()), float(sal.max())
    if smax > smin:
        sal_n = (sal - smin) / (smax - smin)
    else:
        sal_n = sal * 0.0

    # optional downsample
    out_size = input_obj.get("output_size")
    if isinstance(out_size, (list, tuple)) and len(out_size) == 2:
        # simple pooling via downsample helper expects (max_w, max_h)
        # we'll resample roughly by downsampling to requested size via scale ratios
        # Here, use a quick block-mean approach
        H, W = sal_n.shape
        w, h = int(out_size[0]), int(out_size[1])
        w = max(8, min(W, w)); h = max(8, min(H, h))
        sx = W // w if W // w > 0 else 1
        sy = H // h if H // h > 0 else 1
        sal_n = sal_n[:h*sy, :w*sx]
        sal_n = sal_n.reshape(h, sy, w, sx).mean(axis=(1,3))

    heatmap: List[List[float]] = sal_n.astype(np.float32).tolist()
    return {"heatmap": heatmap}

