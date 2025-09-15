"""
MCP Server Implementation for PresentationPro Tools

This server exposes all ADK tools via the Model Context Protocol (MCP).
It provides a standardized interface for tool discovery, execution, and management.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ValidationError

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp.server.fastmcp import FastMCP
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool as MCPTool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .schemas import (
    MCPRequest,
    MCPResponse,
    ListToolsRequest,
    ListToolsResponse,
    CallToolRequest,
    CallToolResponse,
    ToolDefinition,
    ErrorResponse,
    HealthResponse,
)
from .tool_registry import ToolRegistry
from .tool_wrappers import (
    ArangoRAGWrapper,
    WebSearchWrapper,
    VisionWrapper,
    TelemetryWrapper,
    AssetsWrapper,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/mcp_server.log"),
    ],
)
logger = logging.getLogger(__name__)


class MCPServer:
    """Main MCP Server implementation"""

    def __init__(self, name: str = "PresentationPro MCP Server"):
        self.name = name
        self.mcp = FastMCP(name)
        self.registry = ToolRegistry()
        self.app = FastAPI(title=name, version="1.0.0")
        self._setup_middleware()
        self._setup_routes()
        self._register_tools()
        self._setup_lifespan()

    def _setup_middleware(self):
        """Configure middleware for the FastAPI app"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Setup FastAPI routes for MCP protocol"""

        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint"""
            return HealthResponse(
                status="healthy",
                server_name=self.name,
                tools_count=len(self.registry.list_tools()),
                uptime_seconds=0,  # TODO: Track actual uptime
            )

        @self.app.post("/tools/list", response_model=ListToolsResponse)
        async def list_tools(request: ListToolsRequest):
            """List all available tools"""
            try:
                tools = self.registry.list_tools()
                return ListToolsResponse(tools=tools)
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/tools/call", response_model=CallToolResponse)
        async def call_tool(request: CallToolRequest):
            """Execute a specific tool"""
            try:
                result = await self.registry.execute_tool(
                    request.name, request.arguments
                )
                return CallToolResponse(
                    name=request.name,
                    content=[TextContent(type="text", text=json.dumps(result))],
                    isError=False,
                )
            except ValueError as e:
                logger.error(f"Tool not found: {e}")
                return CallToolResponse(
                    name=request.name,
                    content=[TextContent(type="text", text=str(e))],
                    isError=True,
                )
            except Exception as e:
                logger.error(f"Error executing tool {request.name}: {e}")
                return CallToolResponse(
                    name=request.name,
                    content=[TextContent(type="text", text=f"Execution error: {str(e)}")],
                    isError=True,
                )

        @self.app.post("/mcp", response_class=StreamingResponse)
        async def mcp_endpoint(request: Request):
            """Main MCP protocol endpoint for streaming"""
            try:
                body = await request.body()
                # Process MCP protocol messages
                return StreamingResponse(
                    self._process_mcp_stream(body),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "X-Accel-Buffering": "no",
                    },
                )
            except Exception as e:
                logger.error(f"MCP endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Mount MCP server's streamable HTTP app
        self.app.mount("/mcp/stream", self.mcp.streamable_http_app())

    def _register_tools(self):
        """Register all tool wrappers with the registry and MCP server"""

        # Initialize tool wrappers
        arango_wrapper = ArangoRAGWrapper()
        search_wrapper = WebSearchWrapper()
        vision_wrapper = VisionWrapper()
        telemetry_wrapper = TelemetryWrapper()
        assets_wrapper = AssetsWrapper()

        # Register with internal registry
        self.registry.register_tool("arango_rag_ingest", arango_wrapper)
        self.registry.register_tool("arango_rag_retrieve", arango_wrapper)
        self.registry.register_tool("web_search", search_wrapper)
        self.registry.register_tool("vision_analyze", vision_wrapper)
        self.registry.register_tool("telemetry_record", telemetry_wrapper)
        self.registry.register_tool("telemetry_aggregate", telemetry_wrapper)
        self.registry.register_tool("assets_ingest", assets_wrapper)

        # Register with MCP server using decorators
        self._register_mcp_tools()

    def _register_mcp_tools(self):
        """Register tools with the MCP server using FastMCP decorators"""

        @self.mcp.tool()
        async def arango_rag_ingest(
            presentationId: str,
            assets: List[Dict[str, Any]],
        ) -> Dict[str, Any]:
            """Ingest documents into ArangoDB for RAG retrieval"""
            wrapper = self.registry.get_tool("arango_rag_ingest")
            return await wrapper.execute("ingest", {
                "presentationId": presentationId,
                "assets": assets,
            })

        @self.mcp.tool()
        async def arango_rag_retrieve(
            presentationId: str,
            query: str,
            limit: int = 5,
        ) -> Dict[str, Any]:
            """Retrieve relevant chunks from ArangoDB"""
            wrapper = self.registry.get_tool("arango_rag_retrieve")
            return await wrapper.execute("retrieve", {
                "presentationId": presentationId,
                "query": query,
                "limit": limit,
            })

        @self.mcp.tool()
        async def web_search(
            query: str,
            top_k: int = 5,
            allow_domains: Optional[List[str]] = None,
        ) -> List[Dict[str, str]]:
            """Search the web for information"""
            wrapper = self.registry.get_tool("web_search")
            return await wrapper.execute("search", {
                "query": query,
                "top_k": top_k,
                "allow_domains": allow_domains,
            })

        @self.mcp.tool()
        async def vision_analyze(
            screenshotDataUrl: str,
        ) -> Dict[str, Any]:
            """Analyze image for contrast and visibility"""
            wrapper = self.registry.get_tool("vision_analyze")
            return await wrapper.execute("analyze", {
                "screenshotDataUrl": screenshotDataUrl,
            })

        @self.mcp.tool()
        async def telemetry_record(
            step: str,
            agent: Optional[str] = None,
            model: Optional[str] = None,
            promptTokens: int = 0,
            completionTokens: int = 0,
            durationMs: int = 0,
            meta: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            """Record telemetry event"""
            wrapper = self.registry.get_tool("telemetry_record")
            return await wrapper.execute("record", {
                "step": step,
                "agent": agent,
                "model": model,
                "promptTokens": promptTokens,
                "completionTokens": completionTokens,
                "durationMs": durationMs,
                "meta": meta or {},
            })

        @self.mcp.tool()
        async def telemetry_aggregate() -> Dict[str, Any]:
            """Get aggregated telemetry statistics"""
            wrapper = self.registry.get_tool("telemetry_aggregate")
            return await wrapper.execute("aggregate", {})

        @self.mcp.tool()
        async def assets_ingest(
            presentationId: str,
            assets: List[Dict[str, Any]],
        ) -> Dict[str, Any]:
            """Process and ingest uploaded assets"""
            wrapper = self.registry.get_tool("assets_ingest")
            return await wrapper.execute("ingest", {
                "presentationId": presentationId,
                "assets": assets,
            })

    def _setup_lifespan(self):
        """Setup lifespan management for the server"""

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncIterator[None]:
            """Manage server lifecycle"""
            logger.info(f"Starting {self.name}")
            # Initialize resources
            await self.registry.initialize()
            yield
            # Cleanup resources
            logger.info(f"Shutting down {self.name}")
            await self.registry.cleanup()

        self.app.router.lifespan_context = lifespan

    async def _process_mcp_stream(self, body: bytes) -> AsyncIterator[str]:
        """Process MCP protocol streaming messages"""
        try:
            # Parse incoming message
            message = json.loads(body)

            # Handle different message types
            if message.get("method") == "tools/list":
                tools = self.registry.list_tools()
                response = {"jsonrpc": "2.0", "result": {"tools": tools}}
                yield f"data: {json.dumps(response)}\n\n"

            elif message.get("method") == "tools/call":
                params = message.get("params", {})
                result = await self.registry.execute_tool(
                    params.get("name"),
                    params.get("arguments", {})
                )
                response = {
                    "jsonrpc": "2.0",
                    "result": {"content": [{"type": "text", "text": json.dumps(result)}]}
                }
                yield f"data: {json.dumps(response)}\n\n"

            else:
                # Unknown method
                response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": "Method not found"}
                }
                yield f"data: {json.dumps(response)}\n\n"

        except json.JSONDecodeError as e:
            response = {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"}
            }
            yield f"data: {json.dumps(response)}\n\n"
        except Exception as e:
            logger.error(f"Stream processing error: {e}")
            response = {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": "Internal error"}
            }
            yield f"data: {json.dumps(response)}\n\n"

    def run_stdio(self):
        """Run the server in stdio mode for MCP protocol"""
        asyncio.run(self._run_stdio())

    async def _run_stdio(self):
        """Async stdio server runner"""
        async with stdio_server() as (read_stream, write_stream):
            await self.mcp.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=self.name,
                    server_version="1.0.0",
                    capabilities=self.mcp.get_capabilities(),
                ),
            )

    def run_http(self, host: str = "0.0.0.0", port: int = 8090):
        """Run the server in HTTP mode"""
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
        )

    def run_streamable_http(self, host: str = "0.0.0.0", port: int = 8090):
        """Run the server in streamable HTTP mode"""
        self.mcp.run(
            transport="streamable-http",
            host=host,
            port=port,
        )


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="PresentationPro MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "streamable-http"],
        default="streamable-http",
        help="Transport mode for the server",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server (for HTTP modes)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8090,
        help="Port to bind the server (for HTTP modes)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )

    args = parser.parse_args()

    # Configure logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Create and run server
    server = MCPServer()

    if args.transport == "stdio":
        logger.info("Starting MCP server in stdio mode")
        server.run_stdio()
    elif args.transport == "http":
        logger.info(f"Starting MCP server in HTTP mode on {args.host}:{args.port}")
        server.run_http(args.host, args.port)
    else:  # streamable-http
        logger.info(f"Starting MCP server in streamable HTTP mode on {args.host}:{args.port}")
        server.run_streamable_http(args.host, args.port)


if __name__ == "__main__":
    main()