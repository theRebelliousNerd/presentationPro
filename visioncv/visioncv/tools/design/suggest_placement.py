from typing import Any, Dict, List, Optional, Tuple

import math
import numpy as np
from PIL import Image

from ..util.images import decode_data_url
from .saliency_spectral import saliency_spectral
from .empty_regions import find_empty_regions

# Golden ratio constant
PHI = 1.618033988749


def _thirds_points(w: int, h: int) -> List[Tuple[float, float]]:
    xs = [w/3.0, 2.0*w/3.0]
    ys = [h/3.0, 2.0*h/3.0]
    return [(x, y) for x in xs for y in ys]


def _golden_points(w: int, h: int) -> List[Tuple[float, float]]:
    """Generate golden ratio grid points."""
    # Golden ratio divides the frame at PHI-1 ≈ 0.618 and 1/PHI ≈ 0.618 from each side
    golden_ratio = 1.0 / PHI  # ≈ 0.618
    xs = [w * golden_ratio, w * (1.0 - golden_ratio)]
    ys = [h * golden_ratio, h * (1.0 - golden_ratio)]
    return [(x, y) for x in xs for y in ys]


def _fibonacci_spiral_points(w: int, h: int) -> List[Tuple[float, float]]:
    """Generate focal points along Fibonacci spiral."""
    # Create fibonacci spiral quarters and find focal points
    points = []

    # Use golden ratio to create spiral quarters
    # Each quarter has a focal point at approximately 1/3 from the corner
    quarter_w, quarter_h = w / 2.0, h / 2.0

    # Four spiral quarters with focal points
    quarters = [
        (0, 0, quarter_w, quarter_h),           # Top-left
        (quarter_w, 0, quarter_w, quarter_h),   # Top-right
        (quarter_w, quarter_h, quarter_w, quarter_h),  # Bottom-right
        (0, quarter_h, quarter_w, quarter_h),   # Bottom-left
    ]

    for qx, qy, qw, qh in quarters:
        # Focal point at golden ratio position within quarter
        focal_x = qx + qw / PHI
        focal_y = qy + qh / PHI
        points.append((focal_x, focal_y))

    return points


def _diagonal_points(w: int, h: int) -> List[Tuple[float, float]]:
    """Generate intersection points along image diagonals."""
    points = []

    # Main diagonal (top-left to bottom-right)
    # Sample points at golden ratio intervals
    for i in range(1, 4):  # 3 points along diagonal
        t = i / 4.0  # 0.25, 0.5, 0.75
        points.append((w * t, h * t))

    # Anti-diagonal (top-right to bottom-left)
    for i in range(1, 4):  # 3 points along anti-diagonal
        t = i / 4.0
        points.append((w * (1.0 - t), h * t))

    return points


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


def _nearest_golden_distance(cx: float, cy: float, golden: List[Tuple[float,float]]) -> float:
    """Calculate distance to nearest golden ratio point."""
    best = 1e9
    for gx, gy in golden:
        d = math.hypot(cx - gx, cy - gy)
        if d < best:
            best = d
    return best


def _nearest_fibonacci_distance(cx: float, cy: float, fibonacci: List[Tuple[float,float]]) -> float:
    """Calculate distance to nearest fibonacci spiral focal point."""
    best = 1e9
    for fx, fy in fibonacci:
        d = math.hypot(cx - fx, cy - fy)
        if d < best:
            best = d
    return best


def _nearest_diagonal_distance(cx: float, cy: float, diagonal: List[Tuple[float,float]]) -> float:
    """Calculate distance to nearest diagonal intersection point."""
    best = 1e9
    for dx, dy in diagonal:
        d = math.hypot(cx - dx, cy - dy)
        if d < best:
            best = d
    return best


def _calculate_visual_weight(img_array: np.ndarray, x: int, y: int, w: int, h: int) -> float:
    """Calculate visual weight of a region based on color intensity and contrast."""
    height, width = img_array.shape[:2]
    x2 = min(width, x + w)
    y2 = min(height, y + h)

    if x2 <= x or y2 <= y:
        return 0.0

    region = img_array[y:y2, x:x2]

    # Convert to grayscale if color
    if len(region.shape) == 3:
        # Use luminance formula for perceived brightness
        gray = 0.299 * region[:,:,0] + 0.587 * region[:,:,1] + 0.114 * region[:,:,2]
    else:
        gray = region

    # Calculate visual weight factors
    # 1. Mean intensity (darker = more weight)
    mean_intensity = float(gray.mean()) / 255.0
    intensity_weight = 1.0 - mean_intensity

    # 2. Contrast (higher std = more weight)
    contrast_weight = float(gray.std()) / 255.0

    # 3. Size factor (larger = more weight, but with diminishing returns)
    area = (x2 - x) * (y2 - y)
    total_area = width * height
    size_weight = math.sqrt(area / total_area)

    # Combine factors
    visual_weight = (intensity_weight * 0.4 + contrast_weight * 0.4 + size_weight * 0.2)
    return min(1.0, visual_weight)


def suggest_placement(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Suggest placement regions using advanced composition algorithms.

    Inputs:
      - screenshotDataUrl or imageDataUrl
      - preference?: 'near_salient' | 'away_from_salient' (default: away_from_salient)
      - composition_mode?: 'thirds' | 'golden' | 'fibonacci' | 'diagonal' | 'combined' (default: combined)
      - weights?: { area?: number, composition?: number, saliency?: number, visual_weight?: number }
      - min_area_pixels?: number

    Output:
      { candidates: [ { bounding_box, area, score, composition_scores, mean_saliency, visual_weight } ],
        width, height, composition_grid }
    """
    data_url = input_obj.get("screenshotDataUrl") or input_obj.get("imageDataUrl")
    if not data_url:
        raise ValueError("Missing 'screenshotDataUrl' or 'imageDataUrl'")
    img = decode_data_url(data_url)
    h, w = img.size[1], img.size[0]

    # Convert PIL image to numpy array for visual weight calculation
    img_array = np.array(img)

    # Get composition mode
    composition_mode = input_obj.get("composition_mode", "combined").lower()

    # Generate composition points based on mode
    composition_points = {}
    composition_grid = {}

    if composition_mode in ["thirds", "combined"]:
        thirds = _thirds_points(w, h)
        composition_points["thirds"] = thirds
        composition_grid["thirds"] = thirds

    if composition_mode in ["golden", "combined"]:
        golden = _golden_points(w, h)
        composition_points["golden"] = golden
        composition_grid["golden"] = golden

    if composition_mode in ["fibonacci", "combined"]:
        fibonacci = _fibonacci_spiral_points(w, h)
        composition_points["fibonacci"] = fibonacci
        composition_grid["fibonacci"] = fibonacci

    if composition_mode in ["diagonal", "combined"]:
        diagonal = _diagonal_points(w, h)
        composition_points["diagonal"] = diagonal
        composition_grid["diagonal"] = diagonal

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
        return {"candidates": [], "width": w, "height": h, "composition_grid": composition_grid}

    pref = (input_obj.get("preference") or "away_from_salient").lower()
    weights = input_obj.get("weights") or {}
    wa = float(weights.get("area", 0.3))
    wc = float(weights.get("composition", 0.4))
    ws = float(weights.get("saliency", 0.2))
    wv = float(weights.get("visual_weight", 0.1))

    # Precompute diagonal for normalization
    diag = math.hypot(w, h)
    total_area = float(w * h)

    scored: List[Dict[str, Any]] = []
    for r in regions:
        bb = r.get("bounding_box") or {}
        x = int(bb.get("x", 0)); y = int(bb.get("y", 0))
        ww = int(bb.get("width", 0)); hh = int(bb.get("height", 0))
        area = int(r.get("area", ww * hh))
        cx, cy = _region_center(r)

        # Calculate composition scores for each enabled algorithm
        composition_scores = {}
        best_composition_score = 0.0

        if "thirds" in composition_points:
            d_thirds = _nearest_thirds_distance(cx, cy, composition_points["thirds"])
            thirds_score = 1.0 - min(1.0, d_thirds / diag)
            composition_scores["thirds"] = round(float(thirds_score), 4)
            best_composition_score = max(best_composition_score, thirds_score)

        if "golden" in composition_points:
            d_golden = _nearest_golden_distance(cx, cy, composition_points["golden"])
            golden_score = 1.0 - min(1.0, d_golden / diag)
            composition_scores["golden"] = round(float(golden_score), 4)
            best_composition_score = max(best_composition_score, golden_score)

        if "fibonacci" in composition_points:
            d_fibonacci = _nearest_fibonacci_distance(cx, cy, composition_points["fibonacci"])
            fibonacci_score = 1.0 - min(1.0, d_fibonacci / diag)
            composition_scores["fibonacci"] = round(float(fibonacci_score), 4)
            best_composition_score = max(best_composition_score, fibonacci_score)

        if "diagonal" in composition_points:
            d_diagonal = _nearest_diagonal_distance(cx, cy, composition_points["diagonal"])
            diagonal_score = 1.0 - min(1.0, d_diagonal / diag)
            composition_scores["diagonal"] = round(float(diagonal_score), 4)
            best_composition_score = max(best_composition_score, diagonal_score)

        # For combined mode, use the best composition score
        if composition_mode == "combined" and composition_scores:
            final_composition_score = best_composition_score
        elif len(composition_scores) == 1:
            final_composition_score = list(composition_scores.values())[0]
        else:
            # Average multiple scores if specific mode selected
            final_composition_score = sum(composition_scores.values()) / len(composition_scores) if composition_scores else 0.0

        # Mean saliency inside region
        x2 = min(w, x + ww); y2 = min(h, y + hh)
        if x2 <= x or y2 <= y:
            mean_sal = 1.0
        else:
            mean_sal = float(sal_full[y:y2, x:x2].mean())
        sal_term = (1.0 - mean_sal) if pref == "away_from_salient" else mean_sal

        # Calculate visual weight
        visual_weight = _calculate_visual_weight(img_array, x, y, ww, hh)
        visual_weight_term = 1.0 - visual_weight  # Lower visual weight = better for placement

        # Final score combining all factors
        score = (wa * (area / total_area) +
                wc * final_composition_score +
                ws * sal_term +
                wv * visual_weight_term)

        scored.append({
            "bounding_box": {"x": x, "y": y, "width": ww, "height": hh},
            "area": area,
            "score": round(float(score), 4),
            "composition_scores": composition_scores,
            "mean_saliency": round(float(mean_sal), 4),
            "visual_weight": round(float(visual_weight), 4),
        })

    scored.sort(key=lambda k: k["score"], reverse=True)
    return {
        "candidates": scored[:10],
        "width": w,
        "height": h,
        "composition_grid": composition_grid
    }

