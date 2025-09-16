from typing import Any, Dict, List, Tuple

import math

from ..design.palette import extract_palette as _extract_palette


def _hex_to_rgb_tuple(hex_color: str) -> Tuple[int, int, int]:
    s = hex_color.strip().lstrip('#')
    if len(s) == 3:
        s = ''.join([c*2 for c in s])
    if len(s) != 6:
        raise ValueError("Invalid hex color")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def _dist_sq(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    return float((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)


def validate_brand_colors(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Compare image palette to brand palette.

    Inputs: { imageDataUrl: string, brandPalette: ["#rrggbb", ...], tolerance?: number }
    Output: { coverage: number, matches: [{brand: "#..", nearest: "#..", distance: number, fraction: number}], missing: ["#.."], extras: ["#.."] }
    """
    imageDataUrl = input_obj.get("imageDataUrl") or input_obj.get("screenshotDataUrl")
    if not imageDataUrl:
        raise ValueError("Missing 'imageDataUrl' or 'screenshotDataUrl'")
    brand = input_obj.get("brandPalette") or []
    if not isinstance(brand, list) or not brand:
        raise ValueError("Provide non-empty 'brandPalette' list of hex colors")
    tol = float(input_obj.get("tolerance") or 60.0)

    pal = _extract_palette({"imageDataUrl": imageDataUrl, "colors": 10})["palette"]
    # Map brand colors to nearest palette color
    brand_rgb = [(_hex_to_rgb_tuple(h), h) for h in brand]
    matches = []
    matched_palette_idx = set()
    for brgb, bhex in brand_rgb:
        best_idx = -1
        best_dist = 1e9
        best_pal = None
        for idx, p in enumerate(pal):
            prgb = tuple(p["rgb"])  # type: ignore
            d = _dist_sq(brgb, (int(prgb[0]), int(prgb[1]), int(prgb[2])))
            if d < best_dist:
                best_dist = d
                best_idx = idx
                best_pal = p
        if best_pal is not None:
            matched_palette_idx.add(best_idx)
            matches.append({
                "brand": bhex,
                "nearest": best_pal["hex"],
                "distance": round(math.sqrt(best_dist), 2),
                "fraction": best_pal["fraction"],
            })

    coverage = sum(m["fraction"] for m in matches if m["distance"] <= tol)
    missing = [m["brand"] for m in matches if m["distance"] > tol]
    extras = [p["hex"] for i, p in enumerate(pal) if i not in matched_palette_idx]
    return {
        "coverage": round(coverage, 4),
        "matches": matches,
        "missing": missing,
        "extras": extras,
    }

