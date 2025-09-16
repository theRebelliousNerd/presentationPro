from typing import Any, Dict, List, Optional, Tuple

import math
import numpy as np

from ..util.images import decode_data_url
from .saliency_spectral import saliency_spectral
from .empty_regions import find_empty_regions


def _thirds_points(w: int, h: int) -> List[Tuple[float, float]]:
    xs = [w/3.0, 2.0*w/3.0]
    ys = [h/3.0, 2.0*h/3.0]
    return [(x, y) for x in xs for y in ys]


def _region_center(r: Dict[str, Any]) -> Tuple[float, float]:
    bb = r.get("bounding_box") or {}
    x = float(bb.get("x", 0)); y = float(bb.get("y", 0))
    w = float(bb.get("width", 0)); h = float(bb.get("height", 0))
    return (x + w/2.0, y + h/2.0)


def _nearest_thirds_distance(cx: float, cy: float, thirds: List[Tuple[float,float]]) -> float:
    best = 1e9
    for tx, ty in thirds:
        d = math.hypot(cx - tx, cy - ty)
        if d < best:
            best = d
    return best


def suggest_placement(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Suggest placement regions combining empty areas, rule-of-thirds alignment, and saliency.

    Inputs:
      - screenshotDataUrl or imageDataUrl
      - preference?: 'near_salient' | 'away_from_salient' (default: away_from_salient)
      - weights?: { area?: number, thirds?: number, saliency?: number }
      - min_area_pixels?: number

    Output:
      { candidates: [ { bounding_box, area, score, thirds_distance, mean_saliency } ], width, height }
    """
    data_url = input_obj.get("screenshotDataUrl") or input_obj.get("imageDataUrl")
    if not data_url:
        raise ValueError("Missing 'screenshotDataUrl' or 'imageDataUrl'")
    img = decode_data_url(data_url)
    h, w = img.size[1], img.size[0]
    thirds = _thirds_points(w, h)

    # Saliency
    sal = saliency_spectral({"imageDataUrl": data_url})["heatmap"]
    sal_arr = np.array(sal, dtype=np.float32)
    sh, sw = sal_arr.shape
    # rescale saliency to image size via simple nearest sampling
    ys = (np.linspace(0, sh-1, h)).astype(np.int32)
    xs = (np.linspace(0, sw-1, w)).astype(np.int32)
    sal_full = sal_arr[ys][:, xs]

    # Empty regions
    min_area = input_obj.get("min_area_pixels")
    regions = find_empty_regions({"screenshotDataUrl": data_url, "min_area_pixels": min_area}).get("empty_regions", [])

    if not regions:
        return {"candidates": [], "width": w, "height": h}

    pref = (input_obj.get("preference") or "away_from_salient").lower()
    weights = input_obj.get("weights") or {}
    wa = float(weights.get("area", 0.5))
    wt = float(weights.get("thirds", 0.3))
    ws = float(weights.get("saliency", 0.2))

    # Precompute diag for thirds normalization
    diag = math.hypot(w, h)
    total_area = float(w * h)

    scored: List[Dict[str, Any]] = []
    for r in regions:
        bb = r.get("bounding_box") or {}
        x = int(bb.get("x", 0)); y = int(bb.get("y", 0))
        ww = int(bb.get("width", 0)); hh = int(bb.get("height", 0))
        area = int(r.get("area", ww * hh))
        cx, cy = _region_center(r)
        d3 = _nearest_thirds_distance(cx, cy, thirds)
        thirds_score = 1.0 - min(1.0, d3 / diag)
        # mean saliency inside region
        x2 = min(w, x + ww); y2 = min(h, y + hh)
        if x2 <= x or y2 <= y:
            mean_sal = 1.0
        else:
            mean_sal = float(sal_full[y:y2, x:x2].mean())
        sal_term = (1.0 - mean_sal) if pref == "away_from_salient" else mean_sal
        score = wa * (area / total_area) + wt * thirds_score + ws * sal_term
        scored.append({
            "bounding_box": {"x": x, "y": y, "width": ww, "height": hh},
            "area": area,
            "score": round(float(score), 4),
            "thirds_distance": round(float(d3), 2),
            "mean_saliency": round(float(mean_sal), 4),
        })

    scored.sort(key=lambda k: k["score"], reverse=True)
    return {"candidates": scored[:10], "width": w, "height": h}

