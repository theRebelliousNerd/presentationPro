from typing import Any, Dict


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    s = hex_color.strip().lstrip('#')
    if len(s) == 3:
        s = ''.join([c*2 for c in s])
    if len(s) != 6:
        raise ValueError("Invalid hex color")
    r = int(s[0:2], 16) / 255.0
    g = int(s[2:4], 16) / 255.0
    b = int(s[4:6], 16) / 255.0
    return r, g, b


def _linearize(c: float) -> float:
    # sRGB to linear
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rel_luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = [_linearize(c) for c in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def check_color_contrast_ratio(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Compute WCAG contrast ratio between two colors.

    Input: { fg: "#rrggbb", bg: "#rrggbb", level?: "AA"|"AAA", fontSizePx?: number }
    Output: { ratio, passesAA, passesAAA }
    """
    fg = input_obj.get("fg")
    bg = input_obj.get("bg")
    if not fg or not bg:
        raise ValueError("Missing 'fg' or 'bg' hex colors")
    lvl = (input_obj.get("level") or "AA").upper()
    font_size = float(input_obj.get("fontSizePx") or 16)
    large_text = font_size >= 24  # simplification

    L1 = _rel_luminance(_hex_to_rgb(fg))
    L2 = _rel_luminance(_hex_to_rgb(bg))
    Lmax, Lmin = (max(L1, L2), min(L1, L2))
    ratio = (Lmax + 0.05) / (Lmin + 0.05)

    # WCAG thresholds
    aa_thresh = 3.0 if large_text else 4.5
    aaa_thresh = 4.5 if large_text else 7.0
    return {
        "ratio": round(ratio, 2),
        "passesAA": bool(ratio >= aa_thresh),
        "passesAAA": bool(ratio >= aaa_thresh),
        "largeText": large_text,
    }

