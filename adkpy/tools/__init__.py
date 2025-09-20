"""
ADK Tools package

Exports tool classes and a simple registry.
"""

from .arango_graph_rag_tool import ArangoGraphRAGTool, Asset, IngestResponse, RetrieveResponse, RetrievedChunk
from .assets_ingest_tool import AssetsIngestTool, IngestAssetInput, IngestSummary
from .telemetry_tool import TelemetryTool, TelemetryEvent
from .vision_contrast_tool import VisionContrastTool, VisionAnalyzeInput, VisionAnalyzeOutput
from .web_search_tool import WebSearchTool, WebResult
try:
    from workflows.tools import WORKFLOW_TOOLS  # running inside container build context
except ImportError:
    from adkpy.workflows.tools import WORKFLOW_TOOLS  # running from repo root

TOOLS_REGISTRY = {
  "graph_rag": ArangoGraphRAGTool,
  "assets_ingest": AssetsIngestTool,
  "telemetry": TelemetryTool,
  "vision_contrast": VisionContrastTool,
  "web_search": WebSearchTool,
}

WORKFLOW_TOOL_SET = WORKFLOW_TOOLS

