from typing import Any, Dict, Tuple

import numpy as np

from ..util.images import decode_data_url


def _to_cv(img) -> np.ndarray:
    arr = np.array(img.convert("RGB"))
    return arr[:, :, ::-1].copy()  # RGB -> BGR


def detect_logo(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Detect a reference logo within a target image using ORB and homography.

    Inputs: { target_image_b64: string|dataURL, reference_logo_b64: string|dataURL }
    Output: { logo_found: bool, bounding_box?: {x,y,width,height}, match_quality_score?: number, match_count?: int }
    """
    try:
        import cv2  # type: ignore
    except Exception as e:
        raise RuntimeError("Logo detection unavailable: OpenCV not installed") from e

    t_url = input_obj.get("target_image_b64") or input_obj.get("screenshotDataUrl")
    r_url = input_obj.get("reference_logo_b64")
    if not t_url or not r_url:
        raise ValueError("Missing 'target_image_b64' and/or 'reference_logo_b64'")

    t_img = _to_cv(decode_data_url(t_url))
    r_img = _to_cv(decode_data_url(r_url))

    orb = cv2.ORB_create(nfeatures=1000)
    kp1, des1 = orb.detectAndCompute(r_img, None)
    kp2, des2 = orb.detectAndCompute(t_img, None)
    if des1 is None or des2 is None or len(kp1) < 4 or len(kp2) < 4:
        return {"logo_found": False, "match_quality_score": 0.0, "match_count": 0}

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda m: m.distance)
    # take good matches under a distance threshold
    good = [m for m in matches if m.distance < 64]
    if len(good) < 8:
        return {"logo_found": False, "match_quality_score": float(len(good)), "match_count": int(len(good))}

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    if H is None:
        return {"logo_found": False, "match_quality_score": float(len(good)), "match_count": int(len(good))}

    h, w = r_img.shape[:2]
    corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    proj = cv2.perspectiveTransform(corners, H)
    xs = proj[:, 0, 0]
    ys = proj[:, 0, 1]
    x1, y1 = float(xs.min()), float(ys.min())
    x2, y2 = float(xs.max()), float(ys.max())
    bbox = {"x": int(max(0, x1)), "y": int(max(0, y1)), "width": int(max(1, x2 - x1)), "height": int(max(1, y2 - y1))}

    # quality: count of inliers from mask if available
    inliers = int(mask.sum()) if mask is not None else len(good)
    score = float(inliers)
    return {"logo_found": True, "bounding_box": bbox, "match_quality_score": score, "match_count": int(len(good))}
