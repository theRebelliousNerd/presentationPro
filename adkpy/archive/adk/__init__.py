"""
ADK (Agent Development Kit) Core Module

This module provides the foundation for the ADK framework including:
- Agent registration and discovery
- Tool registration
- Dev UI integration
- A2A protocol enhancements
"""

from typing import Dict, List, Any, Optional, Type, Callable
from functools import wraps
import inspect
import logging

logger = logging.getLogger(__name__)

# Global registry for agents
_AGENT_REGISTRY: Dict[str, "RegisteredAgent"] = {}
_TOOL_REGISTRY: Dict[str, "RegisteredTool"] = {}


class RegisteredAgent:
    """Represents a registered agent with metadata."""

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        category: str,
        agent_class: Type,
        tools: List[str] = None,
        examples: List[Dict[str, Any]] = None
    ):
        self.name = name
        self.version = version
        self.description = description
        self.category = category
        self.agent_class = agent_class
        self.tools = tools or []
        self.examples = examples or []
        self.instance = None  # Lazy instantiation

    def get_instance(self):
        """Get or create the agent instance."""
        if self.instance is None:
            self.instance = self.agent_class()
        return self.instance

    def get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata for discovery."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "tools": self.tools,
            "examples": self.examples,
            "input_schema": self._get_input_schema(),
            "output_schema": self._get_output_schema()
        }

    def _get_input_schema(self) -> Dict[str, Any]:
        """Extract input schema from agent class."""
        # Look for Input class in agent module
        agent_module = inspect.getmodule(self.agent_class)
        if hasattr(agent_module, 'Input'):
            input_class = getattr(agent_module, 'Input')
            if hasattr(input_class, 'model_json_schema'):
                return input_class.model_json_schema()
        return {}

    def _get_output_schema(self) -> Dict[str, Any]:
        """Extract output schema from agent class."""
        # Look for Output class in agent module
        agent_module = inspect.getmodule(self.agent_class)
        if hasattr(agent_module, 'Output'):
            output_class = getattr(agent_module, 'Output')
            if hasattr(output_class, 'model_json_schema'):
                return output_class.model_json_schema()
        return {}


class RegisteredTool:
    """Represents a registered tool with metadata."""

    def __init__(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Dict[str, Any] = None
    ):
        self.name = name
        self.description = description
        self.function = function
        self.parameters = parameters or self._extract_parameters()

    def _extract_parameters(self) -> Dict[str, Any]:
        """Extract parameters from function signature."""
        sig = inspect.signature(self.function)
        params = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            param_info = {
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                "required": param.default == inspect.Parameter.empty
            }
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
            params[param_name] = param_info
        return params


def agent(
    name: str,
    version: str = "1.0.0",
    description: str = "",
    category: str = "llm",
    tools: List[str] = None,
    examples: List[Dict[str, Any]] = None
):
    """
    Decorator to register an agent with the ADK framework.

    Usage:
        @agent(
            name="clarifier",
            version="2.0.0",
            description="Refines user goals through targeted questions",
            category="llm"
        )
        class ClarifierAgent(BaseAgent):
            ...
    """
    def decorator(cls):
        # Register the agent
        registered = RegisteredAgent(
            name=name,
            version=version,
            description=description or cls.__doc__ or "",
            category=category,
            agent_class=cls,
            tools=tools,
            examples=examples
        )
        _AGENT_REGISTRY[name] = registered

        # Add metadata to the class
        cls._adk_metadata = registered.get_metadata()
        cls._adk_name = name

        logger.info(f"Registered agent: {name} v{version}")
        return cls

    return decorator


def tool(name: str, description: str = ""):
    """
    Decorator to register a tool function within an agent.

    Usage:
        @tool("ask_question", description="Ask a clarifying question")
        def ask_clarifying_question(self, context: str) -> str:
            ...
    """
    def decorator(func):
        # Register the tool
        tool_desc = description or func.__doc__ or ""
        registered = RegisteredTool(
            name=name,
            description=tool_desc,
            function=func
        )
        _TOOL_REGISTRY[name] = registered

        # Add metadata to the function
        func._adk_tool_name = name
        func._adk_tool_description = tool_desc

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Can add telemetry/logging here
            return func(*args, **kwargs)

        logger.debug(f"Registered tool: {name}")
        return wrapper

    return decorator


def get_agent(name: str) -> Optional[RegisteredAgent]:
    """Get a registered agent by name."""
    return _AGENT_REGISTRY.get(name)


def get_all_agents() -> Dict[str, RegisteredAgent]:
    """Get all registered agents."""
    return _AGENT_REGISTRY.copy()


def get_tool(name: str) -> Optional[RegisteredTool]:
    """Get a registered tool by name."""
    return _TOOL_REGISTRY.get(name)


def get_all_tools() -> Dict[str, RegisteredTool]:
    """Get all registered tools."""
    return _TOOL_REGISTRY.copy()


def discover_agents() -> List[Dict[str, Any]]:
    """
    Discover all registered agents and return their metadata.
    Used by the Dev UI for agent listing.
    """
    agents = []
    for agent_name, registered_agent in _AGENT_REGISTRY.items():
        agents.append(registered_agent.get_metadata())
    return agents


def clear_registry():
    """Clear all registered agents and tools (mainly for testing)."""
    _AGENT_REGISTRY.clear()
    _TOOL_REGISTRY.clear()


# Export public API
__all__ = [
    'agent',
    'tool',
    'get_agent',
    'get_all_agents',
    'get_tool',
    'get_all_tools',
    'discover_agents',
    'clear_registry',
    'RegisteredAgent',
    'RegisteredTool'
]