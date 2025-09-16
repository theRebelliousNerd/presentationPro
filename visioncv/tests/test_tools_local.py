import base64
import io
from PIL import Image, ImageDraw

from visioncv.tools.contrast import color_contrast
from visioncv.tools.critic.blur import assess_blur
from visioncv.tools.design.saliency import saliency_map
from visioncv.tools.design.saliency_spectral import saliency_spectral
from visioncv.tools.design.empty_regions import find_empty_regions
from visioncv.tools.design.palette import extract_palette
from visioncv.tools.design.suggest_placement import suggest_placement
from visioncv.tools.critic.noise import measure_noise
from visioncv.tools.critic.contrast_ratio import check_color_contrast_ratio
from visioncv.tools.research.bar_chart import extract_data_from_bar_chart
from visioncv.tools.research.line_graph import extract_data_from_line_graph
from visioncv.tools.brand.validate_colors import validate_brand_colors
from visioncv.tools.research.ocr import ocr_extract
from visioncv.tools.brand.logo import detect_logo


def _mk_data_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def test_all():
    # Create simple slide-like image: white bg, black title, gray area
    img = Image.new("RGB", (400, 300), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 380, 60], fill="#000000")  # title bar
    d.rectangle([30, 100, 260, 220], outline="#000000")  # content box
    url = _mk_data_url(img)

    # Contrast
    print("contrast:", color_contrast({"screenshotDataUrl": url}))
    # Blur (should be fairly sharp)
    print("blur:", assess_blur({"imageDataUrl": url}))
    # Noise
    print("noise:", measure_noise({"imageDataUrl": url}))
    # Saliency
    sal = saliency_map({"imageDataUrl": url})
    print("saliency shape:", len(sal["heatmap"]), len(sal["heatmap"][0]) if sal["heatmap"] else 0)
    # Spectral saliency
    sal2 = saliency_spectral({"imageDataUrl": url, "output_size": [80, 45]})
    print("spectral saliency shape:", len(sal2["heatmap"]), len(sal2["heatmap"][0]) if sal2["heatmap"] else 0)
    # Empty regions
    print("empty regions:", find_empty_regions({"imageDataUrl": url, "min_area_pixels": 5000})["empty_regions"][:3])
    # Suggest placement (away from salient)
    sug = suggest_placement({"imageDataUrl": url, "preference": "away_from_salient", "min_area_pixels": 4000})
    print("placement candidates:", sug["candidates"][:2])
    # Palette
    print("palette:", extract_palette({"imageDataUrl": url, "colors": 4}))
    # Brand colors validation (using white/black)
    print("brand validate:", validate_brand_colors({"imageDataUrl": url, "brandPalette": ["#ffffff", "#000000"]}))
    # Contrast ratio between white and black
    print("contrast ratio:", check_color_contrast_ratio({"fg": "#000", "bg": "#fff", "fontSizePx": 16}))

    # Bar chart synthetic
    chart = Image.new("RGB", (300, 200), "white")
    d2 = ImageDraw.Draw(chart)
    # draw three bars
    d2.rectangle([30, 50, 80, 180], fill="#111")
    d2.rectangle([120, 70, 170, 180], fill="#111")
    d2.rectangle([210, 40, 260, 180], fill="#111")
    chart_url = _mk_data_url(chart)
    print("bar chart:", extract_data_from_bar_chart({"imageDataUrl": chart_url}))

    # Line graph synthetic
    lg = Image.new("RGB", (300, 200), "white")
    d5 = ImageDraw.Draw(lg)
    # draw axes
    d5.line((30, 180, 280, 180), fill="#000", width=2)
    d5.line((30, 20, 30, 180), fill="#000", width=2)
    # draw a simple polyline trend
    pts = [(30, 160), (90, 140), (150, 120), (210, 130), (270, 80)]
    d5.line(pts, fill="#111", width=2)
    lg_url = _mk_data_url(lg)
    print("line graph:", extract_data_from_line_graph({"imageDataUrl": lg_url})["normalized"][:5])

    # OCR (may be unavailable without tesseract)
    try:
        ocr_img = Image.new("RGB", (300, 100), "white")
        d3 = ImageDraw.Draw(ocr_img)
        # draw big block letters using rectangles for simplicity
        d3.rectangle([10, 20, 20, 80], fill="#000")
        d3.rectangle([10, 20, 60, 30], fill="#000")  # simple shapes to simulate text
        ocr_url = _mk_data_url(ocr_img)
        print("ocr:", ocr_extract({"imageDataUrl": ocr_url})["text"][:60])
    except Exception as e:
        print("ocr unavailable:", e)

    # Logo detect (may be unavailable without OpenCV)
    try:
        logo_ref = Image.new("RGB", (80, 80), "white")
        d4 = ImageDraw.Draw(logo_ref)
        d4.rectangle([10, 10, 70, 70], outline="#000", width=4)
        ref_url = _mk_data_url(logo_ref)

        target = Image.new("RGB", (300, 200), "white")
        # paste a scaled version of the ref into target
        small = logo_ref.resize((40, 40))
        target.paste(small, (200, 120))
        tgt_url = _mk_data_url(target)
        print("logo:", detect_logo({"target_image_b64": tgt_url, "reference_logo_b64": ref_url}))
    except Exception as e:
        print("logo detection unavailable:", e)

if __name__ == "__main__":
    test_all()
