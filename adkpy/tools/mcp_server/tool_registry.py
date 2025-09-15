"""
Tool Registry for MCP Server

Manages tool registration, discovery, and execution with proper error handling
and metadata management.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field

from .schemas import ToolDefinition, ToolParameter

logger = logging.getLogger(__name__)


class ToolMetadata(BaseModel):
    """Metadata for a registered tool"""

    name: str
    description: str
    version: str = "1.0.0"
    category: str = "general"
    deprecated: bool = False
    deprecation_message: Optional[str] = None
    rate_limit: Optional[int] = None  # requests per minute
    requires_auth: bool = False
    performance_hint: str = "fast"  # fast, moderate, slow
    examples: List[Dict[str, Any]] = Field(default_factory=list)


class ToolWrapper(BaseModel):
    """Base class for tool wrappers"""

    class Config:
        arbitrary_types_allowed = True

    name: str
    handler: Any  # The actual tool handler object
    metadata: ToolMetadata
    is_async: bool = False

    async def execute(self, method: str, arguments: Dict[str, Any]) -> Any:
        """Execute the tool with given arguments"""
        raise NotImplementedError


class ToolRegistry:
    """Registry for managing tools"""

    def __init__(self):
        self._tools: Dict[str, ToolWrapper] = {}
        self._categories: Dict[str, List[str]] = {}
        self._initialized = False
        self._rate_limiters: Dict[str, Any] = {}

    async def initialize(self):
        """Initialize the registry and all tools"""
        if self._initialized:
            return

        logger.info("Initializing tool registry")

        # Initialize any shared resources
        # This could include database connections, cache, etc.

        self._initialized = True
        logger.info(f"Tool registry initialized with {len(self._tools)} tools")

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up tool registry")

        # Cleanup any shared resources
        for tool_name, wrapper in self._tools.items():
            try:
                if hasattr(wrapper.handler, "cleanup"):
                    if asyncio.iscoroutinefunction(wrapper.handler.cleanup):
                        await wrapper.handler.cleanup()
                    else:
                        wrapper.handler.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up tool {tool_name}: {e}")

        self._initialized = False

    def register_tool(
        self,
        name: str,
        handler: Any,
        metadata: Optional[ToolMetadata] = None,
    ):
        """Register a tool with the registry"""
        if name in self._tools:
            logger.warning(f"Tool {name} already registered, overwriting")

        # Extract metadata if not provided
        if metadata is None:
            metadata = self._extract_metadata(name, handler)

        # Check if handler methods are async
        is_async = self._is_async_handler(handler)

        # Create wrapper
        wrapper = ToolWrapper(
            name=name,
            handler=handler,
            metadata=metadata,
            is_async=is_async,
        )

        # Store in registry
        self._tools[name] = wrapper

        # Update categories
        category = metadata.category
        if category not in self._categories:
            self._categories[category] = []
        if name not in self._categories[category]:
            self._categories[category].append(name)

        logger.info(f"Registered tool: {name} (category: {category})")

    def unregister_tool(self, name: str):
        """Unregister a tool"""
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")

        wrapper = self._tools[name]
        category = wrapper.metadata.category

        # Remove from tools
        del self._tools[name]

        # Remove from categories
        if category in self._categories:
            self._categories[category].remove(name)
            if not self._categories[category]:
                del self._categories[category]

        logger.info(f"Unregistered tool: {name}")

    def get_tool(self, name: str) -> Any:
        """Get a tool handler by name"""
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")

        wrapper = self._tools[name]

        # Check if deprecated
        if wrapper.metadata.deprecated:
            logger.warning(
                f"Tool {name} is deprecated: {wrapper.metadata.deprecation_message}"
            )

        return wrapper.handler

    def list_tools(self) -> List[ToolDefinition]:
        """List all available tools"""
        tools = []

        for name, wrapper in self._tools.items():
            # Skip deprecated tools unless explicitly requested
            if wrapper.metadata.deprecated:
                continue

            # Create tool definition
            tool_def = self._create_tool_definition(name, wrapper)
            tools.append(tool_def)

        return tools

    def list_tools_by_category(self, category: str) -> List[ToolDefinition]:
        """List tools in a specific category"""
        if category not in self._categories:
            return []

        tools = []
        for name in self._categories[category]:
            wrapper = self._tools[name]
            if not wrapper.metadata.deprecated:
                tool_def = self._create_tool_definition(name, wrapper)
                tools.append(tool_def)

        return tools

    def get_categories(self) -> List[str]:
        """Get all tool categories"""
        return list(self._categories.keys())

    async def execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """Execute a tool with given arguments"""
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")

        wrapper = self._tools[name]

        # Check rate limiting
        if wrapper.metadata.rate_limit and not self._check_rate_limit(name):
            raise Exception(f"Rate limit exceeded for tool {name}")

        # Log execution
        logger.debug(f"Executing tool {name} with arguments: {arguments}")

        try:
            # Determine method to call based on tool name
            method = self._get_method_for_tool(name)

            # Execute based on handler type
            if hasattr(wrapper.handler, "execute"):
                # Wrapper has execute method
                if wrapper.is_async:
                    result = await wrapper.handler.execute(method, arguments)
                else:
                    result = wrapper.handler.execute(method, arguments)
            elif hasattr(wrapper.handler, method):
                # Direct method call
                handler_method = getattr(wrapper.handler, method)
                if asyncio.iscoroutinefunction(handler_method):
                    result = await handler_method(**arguments)
                else:
                    result = handler_method(**arguments)
            else:
                raise AttributeError(f"Method {method} not found on handler")

            logger.debug(f"Tool {name} executed successfully")
            return result

        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            raise

    def _extract_metadata(self, name: str, handler: Any) -> ToolMetadata:
        """Extract metadata from handler"""
        # Try to get docstring
        description = "No description available"
        if hasattr(handler, "__doc__") and handler.__doc__:
            description = handler.__doc__.strip()
        elif hasattr(handler.__class__, "__doc__") and handler.__class__.__doc__:
            description = handler.__class__.__doc__.strip()

        # Determine category based on name or handler
        category = "general"
        if "rag" in name.lower() or "arango" in name.lower():
            category = "retrieval"
        elif "search" in name.lower():
            category = "search"
        elif "vision" in name.lower() or "image" in name.lower():
            category = "vision"
        elif "telemetry" in name.lower():
            category = "monitoring"
        elif "assets" in name.lower() or "ingest" in name.lower():
            category = "ingestion"

        # Determine performance hint
        performance = "fast"
        if "search" in name.lower() or "retrieve" in name.lower():
            performance = "moderate"
        elif "ingest" in name.lower() or "analyze" in name.lower():
            performance = "slow"

        return ToolMetadata(
            name=name,
            description=description,
            category=category,
            performance_hint=performance,
        )

    def _is_async_handler(self, handler: Any) -> bool:
        """Check if handler has async methods"""
        # Check execute method
        if hasattr(handler, "execute"):
            return asyncio.iscoroutinefunction(handler.execute)

        # Check common method names
        for method_name in ["ingest", "retrieve", "search", "analyze", "record"]:
            if hasattr(handler, method_name):
                return asyncio.iscoroutinefunction(getattr(handler, method_name))

        return False

    def _create_tool_definition(
        self,
        name: str,
        wrapper: ToolWrapper,
    ) -> ToolDefinition:
        """Create a tool definition for MCP protocol"""
        # Extract parameters from handler
        parameters = self._extract_parameters(name, wrapper.handler)

        return ToolDefinition(
            name=name,
            description=wrapper.metadata.description,
            inputSchema={
                "type": "object",
                "properties": {
                    param.name: {
                        "type": param.type,
                        "description": param.description,
                        **({"default": param.default} if param.default is not None else {}),
                    }
                    for param in parameters
                },
                "required": [
                    param.name for param in parameters if param.required
                ],
            },
            category=wrapper.metadata.category,
            version=wrapper.metadata.version,
            deprecated=wrapper.metadata.deprecated,
            deprecationMessage=wrapper.metadata.deprecation_message,
            performanceHint=wrapper.metadata.performance_hint,
            examples=wrapper.metadata.examples,
        )

    def _extract_parameters(
        self,
        name: str,
        handler: Any,
    ) -> List[ToolParameter]:
        """Extract parameters from handler method"""
        parameters = []

        # Determine method to inspect
        method = self._get_method_for_tool(name)

        if hasattr(handler, method):
            handler_method = getattr(handler, method)
            sig = inspect.signature(handler_method)

            for param_name, param in sig.parameters.items():
                if param_name in ["self", "cls"]:
                    continue

                # Determine type
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == list or param.annotation == List:
                        param_type = "array"
                    elif param.annotation == dict or param.annotation == Dict:
                        param_type = "object"

                # Check if required
                required = param.default == inspect.Parameter.empty

                # Get default value
                default = None if required else param.default

                parameters.append(
                    ToolParameter(
                        name=param_name,
                        type=param_type,
                        description=f"Parameter {param_name}",
                        required=required,
                        default=default,
                    )
                )

        return parameters

    def _get_method_for_tool(self, name: str) -> str:
        """Get the method name for a tool"""
        # Map tool names to methods
        method_map = {
            "arango_rag_ingest": "ingest",
            "arango_rag_retrieve": "retrieve",
            "web_search": "search",
            "vision_analyze": "analyze",
            "telemetry_record": "record",
            "telemetry_aggregate": "aggregate",
            "assets_ingest": "ingest_assets",
        }

        return method_map.get(name, name.split("_")[-1])

    def _check_rate_limit(self, name: str) -> bool:
        """Check if tool is within rate limit"""
        # Simple rate limiting implementation
        # In production, use a proper rate limiter like aioredis
        return True  # Placeholder

    def get_tool_metadata(self, name: str) -> ToolMetadata:
        """Get metadata for a tool"""
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")

        return self._tools[name].metadata

    def update_tool_metadata(
        self,
        name: str,
        metadata: ToolMetadata,
    ):
        """Update metadata for a tool"""
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")

        self._tools[name].metadata = metadata
        logger.info(f"Updated metadata for tool {name}")

    def deprecate_tool(
        self,
        name: str,
        message: str,
    ):
        """Mark a tool as deprecated"""
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")

        wrapper = self._tools[name]
        wrapper.metadata.deprecated = True
        wrapper.metadata.deprecation_message = message

        logger.warning(f"Tool {name} marked as deprecated: {message}")