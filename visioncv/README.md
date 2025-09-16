VisionCV — OpenCV-based Vision Service for Agents (MCP)

Overview
- Dedicated, stateless MCP server exposing computer-vision tools to agents using FastMCP.
- Service name is VisionCV. Can run over stdio for local tools or HTTP for containerized use.

Why separate
- Isolation: independent runtime and scaling, no coupling to backend app.
- Performance: own Docker image (OpenCV, OCR deps) without bloating web containers.
- Security: strict, stateless tool calls; host/agents own state and policy.

MCP Contract (via FastMCP)
- Tools are defined as annotated Python functions, exposed over MCP.
- Transports:
  - stdio (default for local dev): `fastmcp run visioncv/agent.py`
  - http (recommended for containers): `python -m visioncv.agent --transport http --host 0.0.0.0 --port 9170`

Tool Namespaces (initial)
- Design: `design.saliency_map`, `design.find_empty_regions`, `design.extract_palette`
- Critic: `critic.assess_blur`, `critic.measure_noise`, `critic.color_contrast`, `critic.check_color_contrast_ratio`
- Research: `research.ocr_extract` (placeholder), `research.extract_data_from_bar_chart`, `research.extract_data_from_line_graph` (placeholder)
- Brand: `brand.detect_logo` (placeholder), `brand.validate_brand_colors`

Quickstart
1) Local (stdio)
   - `pip install -r requirements.txt`
   - `fastmcp run visioncv/agent.py`

   Local (HTTP)
   - `python -m visioncv.agent --transport http --host 0.0.0.0 --port 9170`

2) Docker (HTTP transport)
   - `docker build -t visioncv:dev .`
   - `docker run -p 9170:9170 visioncv:dev`

MCP Usage
- Stdio: connect from an MCP host (e.g., Claude desktop) via `fastmcp` or the official MCP host config.
- HTTP: connect a client via FastMCP HTTP transport (see gofastmcp.com for client examples).

Configuration
- Env vars:
  - `VISIONCV_LOG_LEVEL` (default INFO)

Notes
- Some tools require external binaries (e.g., Tesseract, OpenCV). Placeholders return informative errors until enabled.
- All tools are stateless; callers must supply complete inputs.
