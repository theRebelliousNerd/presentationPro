from typing import Any, Dict, List, Tuple

from PIL import Image

from ..util.images import decode_data_url


def _to_hex(rgb: Tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def extract_palette(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Extract dominant colors using PIL's median cut quantization.

    Inputs: { imageDataUrl: string, colors?: number }
    Output: { palette: [{ hex: string, rgb: [r,g,b], fraction: number }] }
    """
    data_url = input_obj.get("imageDataUrl") or input_obj.get("screenshotDataUrl")
    if not data_url:
        raise ValueError("Missing 'imageDataUrl' or 'screenshotDataUrl'")
    n = int(input_obj.get("colors") or 6)
    img = decode_data_url(data_url)
    small = img.resize((128, 128))
    pal_img = small.convert("P", palette=Image.ADAPTIVE, colors=max(1, min(n, 16)))
    palette = pal_img.getpalette()[: pal_img.getcolors().__len__() * 3]
    counts = pal_img.getcolors()
    total = sum(c for c, _ in counts) if counts else 1
    out: List[Dict[str, Any]] = []
    if counts:
        for count, idx in counts:
            base = idx * 3
            r, g, b = palette[base:base+3]
            out.append({
                "hex": _to_hex((r, g, b)),
                "rgb": [int(r), int(g), int(b)],
                "fraction": round(count / total, 4)
            })
    # sort by fraction desc
    out.sort(key=lambda x: x["fraction"], reverse=True)
    return {"palette": out}

