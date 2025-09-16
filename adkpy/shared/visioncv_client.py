from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Iterable


async def _call_tool_async(url: str, name: str, args: Dict[str, Any]) -> Any:
    from fastmcp import Client

    async with Client(url) as client:
        res = await client.call_tool(name, args)
        # Support multiple fastmcp versions: res may be a wrapper or plain list/dict
        if hasattr(res, "data"):
            return getattr(res, "data")
        return res  # type: ignore


async def _list_tools_async(url: str) -> Iterable[Dict[str, Any]]:
    from fastmcp import Client

    async with Client(url) as client:
        res = await client.list_tools()
        # Support both structured and plain results
        tools = getattr(res, "tools", None) or res
        out = []
        for t in tools:
            name = getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else None)
            desc = getattr(t, "description", None) or (t.get("description") if isinstance(t, dict) else None)
            if name:
                out.append({"name": name, "description": desc})
        return out


def _run_sync(coro: "asyncio.Future[Any]") -> Any:
    """Run a coroutine even if a loop is already running."""

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    return asyncio.run(coro)


def call_tool(name: str, args: Dict[str, Any]) -> Any:
    """Synchronous helper to call VisionCV MCP tool over HTTP.

    Requires env VISIONCV_URL (e.g., http://visioncv:9170/mcp).
    """

    url = os.environ.get("VISIONCV_URL")
    if not url:
        raise RuntimeError("VISIONCV_URL not set")
    return _run_sync(_call_tool_async(url, name, args))


def list_tools() -> Any:
    url = os.environ.get("VISIONCV_URL")
    if not url:
        raise RuntimeError("VISIONCV_URL not set")
    return list(_run_sync(_list_tools_async(url)))
