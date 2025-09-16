from typing import Any, Dict, List

import numpy as np
from PIL import Image

from ..util.images import decode_data_url


def extract_data_from_bar_chart(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Naive vertical bar chart extractor for high-contrast charts.

    Assumes white/light background and dark bars. Returns positions and heights.
    Inputs: { imageDataUrl: string }
    Output: { bars: [{ x: int, width: int, height: int }], width, height }
    """
    data_url = input_obj.get("imageDataUrl") or input_obj.get("screenshotDataUrl")
    if not data_url:
        raise ValueError("Missing 'imageDataUrl' or 'screenshotDataUrl'")
    img = decode_data_url(data_url)
    gray = np.asarray(img.convert("L"), dtype=np.float32)
    h, w = gray.shape
    # invert so bars (dark) become high values
    inv = 255.0 - gray
    # normalize 0..1
    inv = (inv - inv.min()) / (inv.max() - inv.min() + 1e-6)
    # vertical projection
    proj = inv.mean(axis=0)
    # threshold to find bar regions
    thr = float(np.percentile(proj, 65))
    mask = proj >= thr
    bars: List[Dict[str, int]] = []
    # group consecutive columns
    start = None
    for x in range(w):
        if mask[x] and start is None:
            start = x
        elif not mask[x] and start is not None:
            end = x - 1
            width = end - start + 1
            # estimate height by scanning from bottom
            col_vals = inv[:, start:end+1].mean(axis=1)
            thr2 = float(np.percentile(col_vals, 60))
            height_px = 0
            for y in range(h-1, -1, -1):
                if col_vals[y] >= thr2:
                    height_px += 1
                elif height_px > 0:
                    break
            bars.append({"x": int(start), "width": int(width), "height": int(height_px)})
            start = None
    if start is not None:
        end = w - 1
        width = end - start + 1
        col_vals = inv[:, start:end+1].mean(axis=1)
        thr2 = float(np.percentile(col_vals, 60))
        height_px = 0
        for y in range(h-1, -1, -1):
            if col_vals[y] >= thr2:
                height_px += 1
            elif height_px > 0:
                break
        bars.append({"x": int(start), "width": int(width), "height": int(height_px)})

    return {"bars": bars, "width": int(w), "height": int(h)}
