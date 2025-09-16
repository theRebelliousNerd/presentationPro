from typing import Any, Dict, List

import numpy as np

from ..util.images import decode_data_url, to_gray_luma, conv2d, downsample


def _maximal_rectangles(binary_zero_one: np.ndarray) -> List[Dict[str, int]]:
    """Find maximal rectangles of zeros using histogram stack method on inverted map.

    Returns list of rectangles as dicts with x,y,width,height and area.
    """
    grid = (binary_zero_one == 0).astype(np.int32)  # 1 where empty
    h, w = grid.shape
    heights = np.zeros(w, dtype=np.int32)
    rects: List[Dict[str, int]] = []
    for i in range(h):
        # update heights
        heights = heights + grid[i]
        heights[grid[i] == 0] = 0
        # largest rectangles in histogram
        stack: List[int] = []
        j = 0
        while j <= w:
            cur_h = heights[j] if j < w else 0
            if not stack or cur_h >= heights[stack[-1]]:
                stack.append(j)
                j += 1
            else:
                top = stack.pop()
                height = heights[top]
                left = stack[-1] + 1 if stack else 0
                right = j - 1
                width = right - left + 1
                area = int(height * width)
                if area > 0 and height > 0 and width > 0:
                    rects.append({"x": left, "y": i - height + 1, "width": width, "height": height, "area": area})
    # deduplicate similar rects by area threshold
    rects.sort(key=lambda r: r["area"], reverse=True)
    unique: List[Dict[str, int]] = []
    seen = set()
    for r in rects:
        key = (r["x"]//1, r["y"]//1, r["width"]//1, r["height"]//1)
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def find_empty_regions(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Find candidate empty regions by thresholding edge energy on a downsampled grid.

    Inputs:
      - layout_image_b64 or screenshotDataUrl
      - min_area_pixels (on original image); default auto
    """
    data_url = input_obj.get("layout_image_b64") or input_obj.get("screenshotDataUrl") or input_obj.get("imageDataUrl")
    if not data_url:
        raise ValueError("Missing image input: 'layout_image_b64' or 'screenshotDataUrl'")
    img = decode_data_url(data_url)
    gray = to_gray_luma(img)
    # edge energy
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    ky = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
    gx = conv2d(gray, kx)
    gy = conv2d(gray, ky)
    mag = np.sqrt(gx * gx + gy * gy)
    small = downsample(mag, (64, 36))
    # threshold: low edge energy considered empty
    # Use a median-based threshold to be more robust
    thr = float(np.percentile(small, 50))
    empty_mask = (small <= thr).astype(np.uint8)
    # Encourage broader empty zones by applying a light blur-and-threshold pass
    smooth = downsample(small, (64, 36))
    thr2 = float(np.percentile(smooth, 55))
    empty_mask = ((small <= thr) | (smooth <= thr2)).astype(np.uint8)

    # find maximal rectangles in empty mask grid space
    rects_grid = _maximal_rectangles(empty_mask)
    # project back to original image coordinates
    h, w = gray.shape
    gh, gw = empty_mask.shape
    sx = w / gw
    sy = h / gh
    regions: List[Dict[str, int]] = []
    for r in rects_grid[:20]:  # top 20 by area
        x = int(r["x"] * sx)
        y = int(r["y"] * sy)
        ww = int(r["width"] * sx)
        hh = int(r["height"] * sy)
        area = ww * hh
        regions.append({"bounding_box": {"x": x, "y": y, "width": ww, "height": hh}, "area": int(area)})

    min_area = int(input_obj.get("min_area_pixels") or max((w*h)//50, 10_000))
    # Filter by area and reasonable aspect ratios (avoid ultra-thin stripes)
    filtered: List[Dict[str, int]] = []
    for r in regions:
        bb = r["bounding_box"]
        ww = int(bb["width"]); hh = int(bb["height"])
        if r["area"] < min_area:
            continue
        if ww <= 0 or hh <= 0:
            continue
        aspect = max(ww/hh, hh/ww)
        if aspect > 12.0:  # overly skinny
            continue
        filtered.append(r)
    regions = filtered
    regions.sort(key=lambda r: r["area"], reverse=True)
    return {"empty_regions": regions}
