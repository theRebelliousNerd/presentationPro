import argparse
import base64
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .tools.contrast import color_contrast
from .tools.critic.blur import assess_blur
from .tools.design.saliency import saliency_map
from .tools.design.empty_regions import find_empty_regions
from .tools.research.ocr import ocr_extract
from .tools.brand.logo import detect_logo

LOG_LEVEL = logging.getLevelName((__import__('os').environ.get('VISIONCV_LOG_LEVEL') or 'INFO').upper())
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("visioncv")

app = FastAPI(title="VisionCV", version="0.1.0", description="JSON-RPC vision tools for agents")


def list_tools_payload() -> Dict[str, Any]:
    return {
        "tools": [
            {
                "name": "critic.color_contrast",
                "description": "Analyze slide screenshot for contrast and visibility heuristics.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "screenshotDataUrl": {"type": "string", "description": "data URI for PNG/JPEG"}
                    },
                    "required": ["screenshotDataUrl"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "mean": {"type": "number"},
                        "variance": {"type": "number"},
                        "recommendDarken": {"type": "boolean"},
                        "overlay": {"type": "number"}
                    },
                    "required": ["mean", "variance", "recommendDarken", "overlay"]
                }
            },
            {
                "name": "critic.assess_blur",
                "description": "Variance of Laplacian blur score.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "screenshotDataUrl": {"type": "string"},
                        "imageDataUrl": {"type": "string"}
                    },
                    "anyOf": [
                        {"required": ["screenshotDataUrl"]},
                        {"required": ["imageDataUrl"]}
                    ]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "blur_score": {"type": "number"},
                        "laplacian_var": {"type": "number"}
                    },
                    "required": ["blur_score", "laplacian_var"]
                }
            },
            {
                "name": "design.saliency_map",
                "description": "Compute a lightweight saliency heatmap (gradient magnitude).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "screenshotDataUrl": {"type": "string"},
                        "imageDataUrl": {"type": "string"}
                    },
                    "anyOf": [
                        {"required": ["screenshotDataUrl"]},
                        {"required": ["imageDataUrl"]}
                    ]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "heatmap": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}}
                    },
                    "required": ["heatmap"]
                }
            },
            {
                "name": "design.find_empty_regions",
                "description": "Detect unoccupied layout regions on a downsampled grid.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "layout_image_b64": {"type": "string"},
                        "screenshotDataUrl": {"type": "string"},
                        "min_area_pixels": {"type": "number"}
                    },
                    "anyOf": [
                        {"required": ["layout_image_b64"]},
                        {"required": ["screenshotDataUrl"]}
                    ]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "empty_regions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "bounding_box": {
                                        "type": "object",
                                        "properties": {"x": {"type": "number"}, "y": {"type": "number"}, "width": {"type": "number"}, "height": {"type": "number"}},
                                        "required": ["x", "y", "width", "height"]
                                    },
                                    "area": {"type": "number"}
                                },
                                "required": ["bounding_box", "area"]
                            }
                        }
                    },
                    "required": ["empty_regions"]
                }
            },
            {
                "name": "research.ocr_extract",
                "description": "OCR with bounding boxes (requires pytesseract).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "imageDataUrl": {"type": "string"}
                    },
                    "required": ["imageDataUrl"]
                },
                "output_schema": {"type": "object"}
            },
            {
                "name": "brand.detect_logo",
                "description": "Logo presence and quality via ORB (requires OpenCV).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_image_b64": {"type": "string"},
                        "reference_logo_b64": {"type": "string"}
                    },
                    "required": ["target_image_b64", "reference_logo_b64"]
                },
                "output_schema": {"type": "object"}
            },
        ]
    }


@app.post("/rpc")
async def rpc(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}, status_code=400)

    method = body.get("method")
    rpc_id = body.get("id")
    params = body.get("params") or {}

    if method == "list_tools":
        return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": list_tools_payload()})

    if method == "call_tool":
        name = (params or {}).get("name")
        input_obj = (params or {}).get("input") or {}
        try:
            if name == "critic.color_contrast":
                result = color_contrast(input_obj)
                return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})
            if name == "critic.assess_blur":
                result = assess_blur(input_obj)
                return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})
            if name == "design.saliency_map":
                result = saliency_map(input_obj)
                return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})
            if name == "design.find_empty_regions":
                result = find_empty_regions(input_obj)
                return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})
            if name == "research.ocr_extract":
                result = ocr_extract(input_obj)
                return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})
            if name == "brand.detect_logo":
                result = detect_logo(input_obj)
                return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": result})
            else:
                return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": f"Tool not found: {name}"}}, status_code=404)
        except Exception as e:
            logger.exception("Tool call failed")
            return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32000, "message": str(e)}}, status_code=500)

    return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": "Method not found"}}, status_code=404)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=9170, type=int)
    args = parser.parse_args()
    import uvicorn
    uvicorn.run("visioncv.server:app", host=args.host, port=args.port, reload=False, access_log=False)


if __name__ == "__main__":
    main()
