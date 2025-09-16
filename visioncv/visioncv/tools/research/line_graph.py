from typing import Any, Dict, List

import numpy as np

from ..util.images import decode_data_url


def extract_data_from_line_graph(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Extract polylines from a simple line graph image.

    Steps:
      - Convert to grayscale; denoise lightly
      - Detect axes using Hough transform; crop ROI within axes
      - Binarize and thin lines via morphology
      - Find contours as candidate series; for each, sample (x,y) points
    Output:
      { width, height, series: [ { points:[{x,y}], normalized:[{x,y}] } ], roi: {x,y,w,h} }
    """
    data_url = input_obj.get("imageDataUrl") or input_obj.get("screenshotDataUrl")
    if not data_url:
        raise ValueError("Missing 'imageDataUrl' or 'screenshotDataUrl'")

    try:
        import cv2  # type: ignore
    except Exception as e:
        raise RuntimeError("OpenCV not available for line graph extraction") from e

    pil_img = decode_data_url(data_url)
    img = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape[:2]

    # Denoise and edge detection
    blur = cv2.GaussianBlur(gray, (5, 5), 1.0)
    edges = cv2.Canny(blur, 50, 150)

    # Hough transform to detect dominant axes (near horizontal and vertical)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80, minLineLength=int(min(w, h)*0.4), maxLineGap=10)
    x_axis_y = None
    y_axis_x = None
    if lines is not None:
        for l in lines[:, 0, :]:
            x1, y1, x2, y2 = l
            dx, dy = x2 - x1, y2 - y1
            if abs(dy) < 3 and abs(dx) > w * 0.4:
                # horizontal line candidate (x-axis)
                y_avg = int((y1 + y2) / 2)
                x_axis_y = y_avg if (x_axis_y is None or y_avg > x_axis_y) else x_axis_y
            if abs(dx) < 3 and abs(dy) > h * 0.4:
                # vertical line candidate (y-axis)
                x_avg = int((x1 + x2) / 2)
                y_axis_x = x_avg if (y_axis_x is None or x_avg < y_axis_x) else y_axis_x

    # Define ROI within axes
    left = int(max(0, (y_axis_x or int(0.1*w)) + 2))
    right = int(min(w, w - 2))
    bottom = int(min(h, (x_axis_y or int(0.9*h)) - 2))
    top = int(max(0, int(0.05*h)))
    if bottom <= top or right <= left:
        # fallback to margin crop
        left = int(0.1*w); right = int(0.95*w)
        top = int(0.05*h); bottom = int(0.9*h)
    roi = gray[top:bottom, left:right]
    rh, rw = roi.shape[:2]

    # Binarize inverted to make lines white
    inv = cv2.bitwise_not(roi)
    thr = cv2.adaptiveThreshold(inv, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 2)
    # Morphological close to connect gaps; then open to remove specks
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morph = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, kernel, iterations=1)
    morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel, iterations=1)
    # Light skeletonization (thin): erode then open
    skel = cv2.morphologyEx(morph, cv2.MORPH_ERODE, kernel, iterations=1)

    # Remove axis remnants: wipe bottom row and left column vicinity
    if x_axis_y is not None:
        morph[max(0, rh-3):rh, :] = 0
    if y_axis_x is not None:
        morph[:, 0:min(3, rw)] = 0

    # Find contours as potential series (coarse grouping)
    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    series: List[Dict[str, Any]] = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < (rw*rh)*0.001:
            continue
        x, y, ww, hh = cv2.boundingRect(cnt)
        # ignore very thin or huge boxes (likely axes leftovers)
        if ww < 10 or hh < 10:
            continue
        if ww > rw*0.98 and hh < rh*0.05:
            continue

        # sample points across x
        # build a mask for this contour
        mask = np.zeros((rh, rw), dtype=np.uint8)
        cv2.drawContours(mask, [cnt], -1, 255, thickness=cv2.FILLED)
        pts_px: List[Dict[str, int]] = []
        pts_norm: List[Dict[str, float]] = []
        xs = np.linspace(x, x+ww-1, num=min(200, ww)).astype(int)
        for cx in xs:
            col = np.where(mask[:, cx] > 0)[0]
            if col.size == 0:
                continue
            # choose topmost (lowest y) to avoid thick lines; better: centroid
            cy = int(col.min())
            gx = cx + left
            gy = cy + top
            pts_px.append({"x": int(gx), "y": int(gy)})
            nx = gx / float(w)
            ny = 1.0 - (gy / float(h))
            pts_norm.append({"x": round(float(nx), 4), "y": round(float(ny), 4)})

        if pts_px:
            series.append({
                "points": pts_px,
                "normalized": pts_norm,
                "bbox": {"x": int(x+left), "y": int(y+top), "width": int(ww), "height": int(hh)},
            })

    # Continuity tracking across columns (refinement; can split merged contours)
    # Build column-wise candidate map from skeleton
    hsv = cv2.cvtColor(img[top:bottom, left:right], cv2.COLOR_RGB2HSV)
    candidates: List[List[dict]] = []
    for cx in range(rw):
        ys = np.where(skel[:, cx] > 0)[0]
        col = []
        for cy in ys:
            hval = int(hsv[cy, cx, 0])  # 0..179
            col.append({"y": int(cy), "h": hval})
        candidates.append(col)

    # Track series: simple nearest-neighbor with color-consistency
    tracks: List[dict] = []  # each: { 'last_y': int, 'h': float, 'pts_px':[], 'pts_norm':[] }
    max_dy = max(2, rh // 20)
    hue_w = 0.25
    for cx in range(rw):
        used = [False] * len(candidates[cx])
        # Try extend existing tracks first
        for t in tracks:
            best = -1
            best_cost = 1e9
            for i, c in enumerate(candidates[cx]):
                if used[i]:
                    continue
                dy = abs(c["y"] - t['last_y'])
                dh = abs((c['h'] - t['h'] + 90) % 180 - 90)
                cost = dy + hue_w * dh
                if dy <= max_dy and cost < best_cost:
                    best_cost = cost
                    best = i
            if best >= 0:
                c = candidates[cx][best]
                used[best] = True
                t['last_y'] = c['y']
                # EMA hue
                t['h'] = 0.8 * t['h'] + 0.2 * c['h']
                gx = cx + left
                gy = c['y'] + top
                t['pts_px'].append({"x": int(gx), "y": int(gy)})
                nx = gx / float(w)
                ny = 1.0 - (gy / float(h))
                t['pts_norm'].append({"x": round(float(nx), 4), "y": round(float(ny), 4)})
        # Start new tracks for unused candidates
        for i, c in enumerate(candidates[cx]):
            if not used[i]:
                gx = cx + left
                gy = c['y'] + top
                tracks.append({
                    'last_y': c['y'], 'h': float(c['h']),
                    'pts_px': [{"x": int(gx), "y": int(gy)}],
                    'pts_norm': [{"x": round(gx/float(w), 4), "y": round(1.0 - gy/float(h), 4)}]
                })

    # Consolidate tracks: filter short tracks and convert to series entries
    # Keep top-N longest tracks to reduce noise
    tracks_sorted = sorted([t for t in tracks if len(t['pts_px']) >= max(30, rw // 8)], key=lambda x: len(x['pts_px']), reverse=True)
    for t in tracks_sorted[:5]:
        series.append({
            "points": t['pts_px'],
            "normalized": t['pts_norm'],
            "bbox": {"x": int(left), "y": int(top), "width": int(rw), "height": int(rh)}
        })

    # sort series by vertical position (top to bottom) using first point
    series.sort(key=lambda s: s['points'][0]['y'] if s.get('points') else 0)

    return {"width": int(w), "height": int(h), "roi": {"x": left, "y": top, "width": rw, "height": rh}, "series": series}
