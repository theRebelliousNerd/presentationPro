"""
MCP Client Wrapper for ADK Agents

Provides a unified client for agents to access tools via the MCP server.
"""

import os
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class MCPToolResult:
    """Result from an MCP tool invocation"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MCPClient:
    """Client for interacting with MCP server"""

    def __init__(self, server_url: Optional[str] = None):
        """
        Initialize MCP client.

        Args:
            server_url: URL of the MCP server. Defaults to env var MCP_SERVER_URL
        """
        self.server_url = server_url or os.getenv("MCP_SERVER_URL", "http://mcp-server:8090")
        self.client = httpx.AsyncClient(timeout=30.0)
        self._request_id = 0

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    def _get_request_id(self) -> str:
        """Generate unique request ID"""
        self._request_id += 1
        return f"req_{self._request_id}"

    async def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available tools from MCP server.

        Args:
            category: Optional category filter

        Returns:
            List of tool definitions
        """
        try:
            request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {"category": category} if category else {},
                "id": self._get_request_id()
            }

            response = await self.client.post(
                self.server_url,
                json=request
            )
            response.raise_for_status()

            data = response.json()
            if "error" in data:
                logger.error(f"MCP error: {data['error']}")
                return []

            return data.get("result", {}).get("tools", [])

        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []

    async def invoke_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> MCPToolResult:
        """
        Invoke a tool via MCP server.

        Args:
            tool_name: Name of the tool to invoke
            arguments: Tool arguments
            timeout: Optional timeout override

        Returns:
            MCPToolResult with tool output
        """
        try:
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": self._get_request_id()
            }

            # Use custom timeout if provided
            client = self.client
            if timeout:
                client = httpx.AsyncClient(timeout=timeout)

            try:
                response = await client.post(
                    self.server_url,
                    json=request
                )
                response.raise_for_status()

                data = response.json()

                if "error" in data:
                    return MCPToolResult(
                        success=False,
                        error=f"MCP error: {data['error'].get('message', 'Unknown error')}"
                    )

                result = data.get("result", {})
                return MCPToolResult(
                    success=True,
                    data=result.get("content"),
                    metadata=result.get("metadata")
                )

            finally:
                if timeout:
                    await client.aclose()

        except httpx.TimeoutException:
            return MCPToolResult(
                success=False,
                error=f"Tool {tool_name} timed out after {timeout or 30} seconds"
            )
        except Exception as e:
            logger.error(f"Failed to invoke tool {tool_name}: {e}")
            return MCPToolResult(
                success=False,
                error=str(e)
            )

    # Convenience methods for specific tools

    async def search_web(
        self,
        query: str,
        num_results: int = 10
    ) -> MCPToolResult:
        """
        Search the web using the web_search tool.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            MCPToolResult with search results
        """
        return await self.invoke_tool(
            "web_search",
            {
                "query": query,
                "num_results": num_results
            }
        )

    async def retrieve_rag(
        self,
        query: str,
        presentation_id: str,
        limit: int = 10
    ) -> MCPToolResult:
        """
        Retrieve documents from RAG using arango_rag_retrieve.

        Args:
            query: Search query
            presentation_id: Presentation context
            limit: Maximum results

        Returns:
            MCPToolResult with retrieved documents
        """
        return await self.invoke_tool(
            "arango_rag_retrieve",
            {
                "query": query,
                "presentationId": presentation_id,
                "limit": limit
            }
        )

    async def analyze_image(
        self,
        image_path: str,
        analysis_type: str = "full"
    ) -> MCPToolResult:
        """
        Analyze an image using vision_analyze tool.

        Args:
            image_path: Path to image file
            analysis_type: Type of analysis

        Returns:
            MCPToolResult with analysis results
        """
        return await self.invoke_tool(
            "vision_analyze",
            {
                "image_path": image_path,
                "analysis_type": analysis_type
            }
        )

    async def record_telemetry(
        self,
        event_type: str,
        data: Dict[str, Any]
    ) -> MCPToolResult:
        """
        Record telemetry event.

        Args:
            event_type: Type of event
            data: Event data

        Returns:
            MCPToolResult with confirmation
        """
        return await self.invoke_tool(
            "telemetry_record",
            {
                "event_type": event_type,
                "data": data
            }
        )


# Singleton instance for reuse
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get or create singleton MCP client"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


async def cleanup_mcp_client():
    """Cleanup singleton MCP client"""
    global _mcp_client
    if _mcp_client:
        await _mcp_client.close()
        _mcp_client = None