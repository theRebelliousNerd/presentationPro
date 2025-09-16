import base64
import io
import os
import time
import requests
from PIL import Image, ImageDraw


def mk_data_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def wait_gateway(url: str, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("Gateway not reachable")


def run():
    base = os.environ.get("GATEWAY", "http://localhost:18088")
    wait_gateway(base + "/health")

    # OCR check
    img = Image.new("RGB", (400, 120), "white")
    d = ImageDraw.Draw(img)
    # Draw a simple high-contrast banner
    d.rectangle([10, 20, 390, 50], fill="#000")
    data_url = mk_data_url(img)
    ocr = requests.post(base + "/v1/visioncv/ocr", json={"imageDataUrl": data_url}).json()
    print("OCR result keys:", list(ocr.keys()))

    # Logo detection check
    ref = Image.new("RGB", (80, 80), "white")
    d2 = ImageDraw.Draw(ref)
    d2.rectangle([8, 8, 72, 72], outline="#000", width=4)
    ref_url = mk_data_url(ref)

    tgt = Image.new("RGB", (320, 200), "white")
    tgt.paste(ref.resize((50, 50)), (240, 130))
    tgt_url = mk_data_url(tgt)
    logo = requests.post(base + "/v1/visioncv/logo", json={"target_image_b64": tgt_url, "reference_logo_b64": ref_url}).json()
    print("Logo result:", logo)

    return {"ocr_ok": isinstance(ocr, dict), "logo_ok": isinstance(logo, dict)}


if __name__ == "__main__":
    print(run())

