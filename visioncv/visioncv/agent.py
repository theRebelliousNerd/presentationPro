import argparse
import os
from typing import Optional

from fastmcp import FastMCP

from .tools.contrast import color_contrast as _color_contrast
from .tools.critic.blur import assess_blur as _assess_blur
from .tools.design.saliency import saliency_map as _saliency_map
from .tools.design.saliency_spectral import saliency_spectral as _saliency_spectral
from .tools.design.empty_regions import find_empty_regions as _find_empty_regions
from .tools.design.palette import extract_palette as _extract_palette
from .tools.design.procedural_texture import generate_procedural_texture as _generate_texture
from .tools.design.suggest_placement import suggest_placement as _suggest_placement
from .tools.research.ocr import ocr_extract as _ocr_extract
from .tools.research.bar_chart import extract_data_from_bar_chart as _extract_bar_chart
from .tools.research.line_graph import extract_data_from_line_graph as _extract_line_graph
from .tools.brand.logo import detect_logo as _detect_logo
from .tools.brand.validate_colors import validate_brand_colors as _validate_brand_colors
from .tools.critic.noise import measure_noise as _measure_noise
from .tools.critic.contrast_ratio import check_color_contrast_ratio as _check_contrast


mcp = FastMCP("VisionCV")


@mcp.tool(name="critic.color_contrast")
def color_contrast(screenshotDataUrl: str) -> dict:
    return _color_contrast({"screenshotDataUrl": screenshotDataUrl})


@mcp.tool(name="critic.assess_blur")
def assess_blur(screenshotDataUrl: Optional[str] = None, imageDataUrl: Optional[str] = None) -> dict:
    return _assess_blur({"screenshotDataUrl": screenshotDataUrl, "imageDataUrl": imageDataUrl})


@mcp.tool(name="design.saliency_map")
def saliency_map(screenshotDataUrl: Optional[str] = None, imageDataUrl: Optional[str] = None) -> dict:
    return _saliency_map({"screenshotDataUrl": screenshotDataUrl, "imageDataUrl": imageDataUrl})


@mcp.tool(name="design.saliency_spectral")
def saliency_spectral(screenshotDataUrl: Optional[str] = None, imageDataUrl: Optional[str] = None, output_size: Optional[list[int]] = None) -> dict:
    return _saliency_spectral({"screenshotDataUrl": screenshotDataUrl, "imageDataUrl": imageDataUrl, "output_size": output_size})


@mcp.tool(name="design.find_empty_regions")
def find_empty_regions(layout_image_b64: Optional[str] = None, screenshotDataUrl: Optional[str] = None, min_area_pixels: Optional[int] = None) -> dict:
    return _find_empty_regions({
        "layout_image_b64": layout_image_b64,
        "screenshotDataUrl": screenshotDataUrl,
        "min_area_pixels": min_area_pixels,
    })


@mcp.tool(name="design.extract_palette")
def extract_palette(imageDataUrl: Optional[str] = None, screenshotDataUrl: Optional[str] = None, colors: Optional[int] = None) -> dict:
    return _extract_palette({
        "imageDataUrl": imageDataUrl or screenshotDataUrl,
        "colors": colors,
    })


@mcp.tool(name="design.generate_procedural_texture")
def generate_procedural_texture(width: Optional[int] = None, height: Optional[int] = None, texture_type: Optional[str] = None, parameters: Optional[dict] = None) -> dict:
    return _generate_texture({
        "width": width,
        "height": height,
        "texture_type": texture_type,
        "parameters": parameters,
    })


@mcp.tool(name="design.suggest_placement")
def suggest_placement(screenshotDataUrl: Optional[str] = None, imageDataUrl: Optional[str] = None, preference: Optional[str] = None, weights: Optional[dict] = None, min_area_pixels: Optional[int] = None) -> dict:
    return _suggest_placement({
        "screenshotDataUrl": screenshotDataUrl or imageDataUrl,
        "preference": preference,
        "weights": weights,
        "min_area_pixels": min_area_pixels,
    })


@mcp.tool(name="research.ocr_extract")
def ocr_extract(imageDataUrl: str) -> dict:
    return _ocr_extract({"imageDataUrl": imageDataUrl})


@mcp.tool(name="research.extract_data_from_bar_chart")
def extract_data_from_bar_chart(imageDataUrl: str) -> dict:
    return _extract_bar_chart({"imageDataUrl": imageDataUrl})


@mcp.tool(name="research.extract_data_from_line_graph")
def extract_data_from_line_graph(imageDataUrl: str) -> dict:
    return _extract_line_graph({"imageDataUrl": imageDataUrl})


@mcp.tool(name="brand.detect_logo")
def detect_logo(target_image_b64: str, reference_logo_b64: str) -> dict:
    return _detect_logo({"target_image_b64": target_image_b64, "reference_logo_b64": reference_logo_b64})


@mcp.tool(name="brand.validate_brand_colors")
def validate_brand_colors(imageDataUrl: str, brandPalette: list[str], tolerance: Optional[float] = None) -> dict:
    return _validate_brand_colors({"imageDataUrl": imageDataUrl, "brandPalette": brandPalette, "tolerance": tolerance})


@mcp.tool(name="critic.measure_noise")
def measure_noise(screenshotDataUrl: Optional[str] = None, imageDataUrl: Optional[str] = None) -> dict:
    return _measure_noise({"screenshotDataUrl": screenshotDataUrl, "imageDataUrl": imageDataUrl})


@mcp.tool(name="critic.check_color_contrast_ratio")
def check_color_contrast_ratio(fg: str, bg: str, level: Optional[str] = None, fontSizePx: Optional[float] = None) -> dict:
    return _check_contrast({"fg": fg, "bg": bg, "level": level, "fontSizePx": fontSizePx})


def main():
    parser = argparse.ArgumentParser(description="Run VisionCV as an MCP server")
    parser.add_argument("--transport", default=os.environ.get("VISIONCV_MCP_TRANSPORT", "http"), choices=["stdio", "http", "sse"])
    parser.add_argument("--host", default=os.environ.get("VISIONCV_HOST", "127.0.0.1"))
    parser.add_argument("--port", default=int(os.environ.get("VISIONCV_PORT", "9170")))
    parser.add_argument("--path", default=os.environ.get("VISIONCV_HTTP_PATH", "/mcp"))
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port, path=args.path)
    else:
        mcp.run(transport="sse", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
