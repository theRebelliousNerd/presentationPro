from typing import Any, Dict, List

import numpy as np
from PIL import Image

from ..util.images import decode_data_url


def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
    # Grayscale and simple adaptive threshold to help OCR
    gray = img.convert("L")
    arr = np.array(gray)
    # simple global threshold fallback
    thr = max(100, int(arr.mean()))
    bin_img = (arr > thr).astype(np.uint8) * 255
    return Image.fromarray(bin_img)


def ocr_extract(input_obj: Dict[str, Any]) -> Dict[str, Any]:
    """OCR with bounding boxes using Tesseract via pytesseract.

    Input: { imageDataUrl: string, lang?: string }
    Output: { text: string, words: [{ text, conf, x, y, width, height }] }
    """
    data_url = input_obj.get("imageDataUrl") or input_obj.get("screenshotDataUrl")
    if not data_url:
        raise ValueError("Missing 'imageDataUrl' or 'screenshotDataUrl'")
    lang = input_obj.get("lang") or "eng"
    img = decode_data_url(data_url)

    try:
        import pytesseract  # type: ignore
    except Exception as e:
        raise RuntimeError("OCR unavailable: pytesseract not installed or tesseract binary missing") from e

    pre = _preprocess_for_ocr(img)
    try:
        data = pytesseract.image_to_data(pre, lang=lang, output_type=pytesseract.Output.DICT)
    except Exception as e:
        raise RuntimeError(f"OCR failed: {e}")

    words: List[Dict[str, Any]] = []
    n = len(data.get("text", []))
    text_out: List[str] = []
    for i in range(n):
        t = (data["text"][i] or "").strip()
        if not t:
            continue
        conf = float(data.get("conf", ["-1"][i])) if isinstance(data.get("conf"), list) else -1
        x = int(data.get("left", [0])[i])
        y = int(data.get("top", [0])[i])
        w = int(data.get("width", [0])[i])
        h = int(data.get("height", [0])[i])
        words.append({"text": t, "conf": conf, "x": x, "y": y, "width": w, "height": h})
        text_out.append(t)

    return {"text": " ".join(text_out).strip(), "words": words}
