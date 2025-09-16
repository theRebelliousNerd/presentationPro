from typing import Any, Dict

import numpy as np

from ..util.images import decode_data_url, to_gray_luma, conv2d


def assess_blur(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Compute variance of Laplacian as blur score.

    Returns:
      - blur_score: float (lower => blurrier)
      - laplacian_var: alias of blur_score
    """
    data_url = input_obj.get("screenshotDataUrl") or input_obj.get("imageDataUrl")
    if not data_url:
        raise ValueError("Missing 'screenshotDataUrl' or 'imageDataUrl'")
    img = decode_data_url(data_url)
    gray = to_gray_luma(img)
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    lap = conv2d(gray, kernel)
    var = float(lap.var())
    return {"blur_score": round(var, 2), "laplacian_var": round(var, 2)}

