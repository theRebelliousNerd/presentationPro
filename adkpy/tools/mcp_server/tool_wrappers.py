"""
Tool Wrapper Classes for MCP Server

Provides wrapper classes for each tool that handle conversion between
MCP protocol and the underlying tool implementations.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

# Import the actual tool implementations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arango_graph_rag_tool import ArangoGraphRAGTool, Asset, IngestResponse, RetrieveResponse
from web_search_tool import WebSearchTool, WebResult
from vision_contrast_tool import VisionContrastTool, VisionAnalyzeInput, VisionAnalyzeOutput
from telemetry_tool import TelemetryTool, TelemetryEvent
from assets_ingest_tool import AssetsIngestTool, IngestAssetInput, IngestSummary
from app.design_sanitize import (
    validate_html, validate_css, validate_svg,
    sanitize_html, sanitize_css, sanitize_svg,
)

logger = logging.getLogger(__name__)


class BaseToolWrapper:
    """Base class for tool wrappers"""

    def __init__(self):
        self.tool = None
        self._initialize_tool()

    def _initialize_tool(self):
        """Initialize the underlying tool"""
        raise NotImplementedError

    async def execute(self, method: str, arguments: Dict[str, Any]) -> Any:
        """Execute a method on the tool"""
        if not hasattr(self, method):
            raise ValueError(f"Method {method} not found on {self.__class__.__name__}")

        handler = getattr(self, method)
        if asyncio.iscoroutinefunction(handler):
            return await handler(**arguments)
        else:
            return handler(**arguments)

    def cleanup(self):
        """Cleanup resources"""
        pass


class ArangoRAGWrapper(BaseToolWrapper):
    """Wrapper for ArangoGraphRAGTool"""

    def _initialize_tool(self):
        """Initialize the ArangoDB RAG tool"""
        try:
            self.tool = ArangoGraphRAGTool()
            logger.info("ArangoGraphRAGTool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ArangoGraphRAGTool: {e}")
            raise

    def ingest(self, presentationId: str, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingest documents into ArangoDB"""
        try:
            # Convert dictionaries to Asset objects
            asset_objects = []
            for asset_dict in assets:
                asset_objects.append(Asset(
                    presentationId=presentationId,
                    name=asset_dict.get("name", ""),
                    url=asset_dict.get("url"),
                    text=asset_dict.get("text"),
                    kind=asset_dict.get("kind"),
                ))

            # Call the tool
            response: IngestResponse = self.tool.ingest(asset_objects)

            return {
                "ok": response.ok,
                "docs": response.docs,
                "chunks": response.chunks,
            }

        except Exception as e:
            logger.error(f"Error in ArangoRAG ingest: {e}")
            return {
                "ok": False,
                "error": str(e),
                "docs": 0,
                "chunks": 0,
            }

    def retrieve(self, presentationId: str, query: str, limit: int = 5) -> Dict[str, Any]:
        """Retrieve relevant chunks from ArangoDB"""
        try:
            # Call the tool
            response: RetrieveResponse = self.tool.retrieve(
                presentation_id=presentationId,
                query=query,
                limit=limit,
            )

            # Convert response to dictionary
            chunks = []
            for chunk in response.chunks:
                chunks.append({
                    "name": chunk.name,
                    "text": chunk.text,
                    "url": chunk.url,
                })

            return {
                "chunks": chunks,
                "count": len(chunks),
            }

        except Exception as e:
            logger.error(f"Error in ArangoRAG retrieve: {e}")
            return {
                "chunks": [],
                "count": 0,
                "error": str(e),
            }


class WebSearchWrapper(BaseToolWrapper):
    """Wrapper for WebSearchTool"""

    def _initialize_tool(self):
        """Initialize the web search tool"""
        try:
            self.tool = WebSearchTool()
            logger.info("WebSearchTool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WebSearchTool: {e}")
            raise

    def search(
        self,
        query: str,
        top_k: int = 5,
        allow_domains: Optional[List[str]] = None,
    ) -> List[Dict[str, str]]:
        """Search the web for information"""
        try:
            # Create tool with domain filtering if specified
            if allow_domains:
                search_tool = WebSearchTool(allow_domains=allow_domains)
            else:
                search_tool = self.tool

            # Perform search
            results: List[WebResult] = search_tool.search(query, top_k)

            # Convert results to dictionaries
            return [
                {
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet,
                }
                for result in results
            ]

        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return []


class VisionWrapper(BaseToolWrapper):
    """Wrapper for VisionContrastTool"""

    def _initialize_tool(self):
        """Initialize the vision analysis tool"""
        try:
            self.tool = VisionContrastTool()
            logger.info("VisionContrastTool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize VisionContrastTool: {e}")
            raise

    def analyze(self, screenshotDataUrl: str) -> Dict[str, Any]:
        """Analyze image for contrast and visibility"""
        try:
            # Create input
            input_data = VisionAnalyzeInput(screenshotDataUrl=screenshotDataUrl)

            # Analyze
            output: VisionAnalyzeOutput = self.tool.analyze(input_data)

            return {
                "mean": output.mean,
                "variance": output.variance,
                "recommendDarken": output.recommendDarken,
                "overlay": output.overlay,
            }

        except Exception as e:
            logger.error(f"Error in vision analysis: {e}")
            return {
                "mean": 128.0,
                "variance": 500.0,
                "recommendDarken": False,
                "overlay": 0.0,
                "error": str(e),
            }


class TelemetryWrapper(BaseToolWrapper):
    """Wrapper for TelemetryTool"""

    def _initialize_tool(self):
        """Initialize the telemetry tool"""
        try:
            # Use environment variable for sink path if available
            sink_path = os.environ.get("MCP_TELEMETRY_SINK", "/tmp/mcp_telemetry.jsonl")
            self.tool = TelemetryTool(sink_path=sink_path)
            logger.info(f"TelemetryTool initialized with sink: {sink_path}")
        except Exception as e:
            logger.error(f"Failed to initialize TelemetryTool: {e}")
            raise

    def record(
        self,
        step: str,
        agent: Optional[str] = None,
        model: Optional[str] = None,
        promptTokens: int = 0,
        completionTokens: int = 0,
        durationMs: int = 0,
        cost: Optional[float] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a telemetry event"""
        try:
            # Create event
            event = TelemetryEvent(
                step=step,
                agent=agent,
                model=model,
                promptTokens=promptTokens,
                completionTokens=completionTokens,
                durationMs=durationMs,
                cost=cost,
                meta=meta or {},
            )

            # Record event
            self.tool.record(event)

            return {
                "ok": True,
                "event": {
                    "step": event.step,
                    "agent": event.agent,
                    "model": event.model,
                    "promptTokens": event.promptTokens,
                    "completionTokens": event.completionTokens,
                    "durationMs": event.durationMs,
                    "at": event.at,
                },
            }

        except Exception as e:
            logger.error(f"Error recording telemetry: {e}")
            return {
                "ok": False,
                "error": str(e),
            }

    def aggregate(self) -> Dict[str, Any]:
        """Get aggregated telemetry statistics"""
        try:
            return self.tool.aggregate()
        except Exception as e:
            logger.error(f"Error aggregating telemetry: {e}")
            return {
                "total": {
                    "events": 0,
                    "promptTokens": 0,
                    "completionTokens": 0,
                    "durationMs": 0,
                },
                "byAgent": {},
                "error": str(e),
            }

    def cleanup(self):
        """Flush telemetry data on cleanup"""
        try:
            self.tool.flush()
        except Exception as e:
            logger.error(f"Error flushing telemetry: {e}")


class AssetsWrapper(BaseToolWrapper):
    """Wrapper for AssetsIngestTool"""

    def _initialize_tool(self):
        """Initialize the assets ingestion tool"""
        try:
            self.tool = AssetsIngestTool()
            logger.info("AssetsIngestTool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AssetsIngestTool: {e}")
            raise

    def ingest_assets(
        self,
        presentationId: str,
        assets: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Process and ingest uploaded assets"""
        try:
            # Convert dictionaries to IngestAssetInput objects
            asset_inputs = []
            for asset_dict in assets:
                asset_inputs.append(IngestAssetInput(
                    presentationId=presentationId,
                    name=asset_dict.get("name", ""),
                    url=asset_dict.get("url"),
                    path=asset_dict.get("path"),
                    kind=asset_dict.get("kind"),
                    text=asset_dict.get("text"),
                ))

            # Process assets
            summary: IngestSummary = self.tool.ingest_assets(asset_inputs)

            return {
                "ok": summary.ok,
                "docs": summary.docs,
                "chunks": summary.chunks,
                "warnings": summary.warnings,
            }

        except Exception as e:
            logger.error(f"Error ingesting assets: {e}")
            return {
                "ok": False,
                "docs": 0,
                "chunks": 0,
                "warnings": [],
                "error": str(e),
            }

    # Alias for backward compatibility
    def ingest(self, presentationId: str, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Alias for ingest_assets"""
        return self.ingest_assets(presentationId, assets)


class CompositeToolWrapper(BaseToolWrapper):
    """Wrapper that combines multiple tools for complex operations"""

    def __init__(self):
        super().__init__()
        self.arango = ArangoRAGWrapper()
        self.search = WebSearchWrapper()
        self.vision = VisionWrapper()
        self.telemetry = TelemetryWrapper()
        self.assets = AssetsWrapper()

    def _initialize_tool(self):
        """No specific tool to initialize for composite wrapper"""
        pass

    async def research_topic(
        self,
        topic: str,
        presentationId: str,
        search_limit: int = 10,
        retrieve_limit: int = 5,
    ) -> Dict[str, Any]:
        """Research a topic using both web search and RAG retrieval"""
        try:
            results = {}

            # Web search
            search_results = self.search.search(topic, search_limit)
            results["web_results"] = search_results

            # RAG retrieval
            rag_results = self.arango.retrieve(presentationId, topic, retrieve_limit)
            results["rag_results"] = rag_results

            # Record telemetry
            self.telemetry.record(
                step="research_topic",
                meta={
                    "topic": topic,
                    "presentationId": presentationId,
                    "web_count": len(search_results),
                    "rag_count": rag_results.get("count", 0),
                },
            )

            return results

        except Exception as e:
            logger.error(f"Error in research_topic: {e}")
            return {
                "web_results": [],
                "rag_results": {"chunks": [], "count": 0},
                "error": str(e),
            }

    async def process_presentation_assets(
        self,
        presentationId: str,
        assets: List[Dict[str, Any]],
        analyze_images: bool = True,
    ) -> Dict[str, Any]:
        """Process all assets for a presentation"""
        try:
            results = {
                "processed_assets": [],
                "image_analyses": [],
                "ingestion_summary": None,
            }

            # Process images if requested
            if analyze_images:
                for asset in assets:
                    if asset.get("kind") == "image" or asset.get("name", "").lower().endswith(
                        (".png", ".jpg", ".jpeg", ".webp", ".gif")
                    ):
                        if asset.get("dataUrl"):
                            analysis = self.vision.analyze(asset["dataUrl"])
                            results["image_analyses"].append({
                                "name": asset.get("name"),
                                "analysis": analysis,
                            })

            # Ingest all assets
            ingestion_result = self.assets.ingest_assets(presentationId, assets)
            results["ingestion_summary"] = ingestion_result

            # Also ingest into RAG system
            rag_result = self.arango.ingest(presentationId, assets)
            results["rag_ingestion"] = rag_result

            # Record telemetry
            self.telemetry.record(
                step="process_presentation_assets",
                meta={
                    "presentationId": presentationId,
                    "asset_count": len(assets),
                    "images_analyzed": len(results["image_analyses"]),
                    "docs_ingested": ingestion_result.get("docs", 0),
                    "chunks_created": ingestion_result.get("chunks", 0),
                },
            )

            return results

        except Exception as e:
            logger.error(f"Error processing presentation assets: {e}")
            return {
                "processed_assets": [],
                "image_analyses": [],
                "ingestion_summary": None,
                "error": str(e),
            }

    def cleanup(self):
        """Cleanup all sub-tools"""
        self.telemetry.cleanup()


class DesignWrapper(BaseToolWrapper):
    """Wrapper for design validation/sanitization utilities"""

    def _initialize_tool(self):
        self.tool = True

    def validate(self, html: str | None = None, css: str | None = None, svg: str | None = None) -> Dict[str, Any]:
        ok = True
        warnings: list[str] = []
        errors: list[str] = []
        if html:
            ok_h, w_h, e_h = validate_html(html)
            ok = ok and ok_h
            warnings += w_h
            errors += e_h
        if css:
            ok_c, w_c, e_c = validate_css(css)
            ok = ok and ok_c
            warnings += w_c
            errors += e_c
        if svg:
            ok_s, w_s, e_s = validate_svg(svg)
            ok = ok and ok_s
            warnings += w_s
            errors += e_s
        return { 'ok': bool(ok), 'warnings': warnings, 'errors': errors }

    def sanitize(self, html: str | None = None, css: str | None = None, svg: str | None = None) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        warnings: list[str] = []
        if html:
            h, w = sanitize_html(html)
            out['html'] = h
            warnings += w
        if css:
            c, w = sanitize_css(css)
            out['css'] = c
            warnings += w
        if svg:
            s, w = sanitize_svg(svg)
            out['svg'] = s
            warnings += w
        out['warnings'] = warnings
        return out
