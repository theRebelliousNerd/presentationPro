"""
Enhanced Base Agent for ADK Framework

This module provides an enhanced BaseAgent class that supports:
- ADK decorators (@agent, @tool)
- Automatic tool registration
- Telemetry and tracing
- Dev UI integration
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, Type
from pydantic import BaseModel, ValidationError
import time
import logging
import inspect
import json

from app.llm import call_text_model
from . import tool

logger = logging.getLogger(__name__)


class AgentUsage(BaseModel):
    """Enhanced usage tracking with additional metrics."""
    model: str
    promptTokens: int = 0
    completionTokens: int = 0
    totalTokens: int = 0
    durationMs: int = 0
    cost: Optional[float] = None
    error: Optional[str] = None


class AgentResult(BaseModel):
    """Enhanced result model with trace information."""
    data: Dict[str, Any]
    usage: AgentUsage
    trace_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ToolCall(BaseModel):
    """Represents a tool call for tracing."""
    name: str
    parameters: Dict[str, Any]
    result: Any
    duration_ms: int
    timestamp: float


class BaseAgent:
    """
    Enhanced base class for ADK agents.
    Provides common functionality including LLM calls, tool management, and telemetry.
    """

    def __init__(self, model: Optional[str] = None) -> None:
        """Initialize the agent with configuration."""
        self.model = model or "googleai/gemini-2.5-flash"
        self.tools = {}
        self.trace_enabled = False
        self.tool_calls = []
        self._register_tools()

    def _register_tools(self):
        """Automatically register methods decorated with @tool."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, '_adk_tool_name'):
                tool_name = method._adk_tool_name
                self.tools[tool_name] = method
                logger.debug(f"Registered tool {tool_name} for {self.__class__.__name__}")

    def enable_tracing(self):
        """Enable tracing for this agent instance."""
        self.trace_enabled = True
        self.tool_calls = []

    def disable_tracing(self):
        """Disable tracing for this agent instance."""
        self.trace_enabled = False

    def get_trace(self) -> List[ToolCall]:
        """Get the trace of tool calls."""
        return self.tool_calls

    def clear_trace(self):
        """Clear the trace of tool calls."""
        self.tool_calls = []

    def llm(
        self,
        prompt_parts: List[Any],
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        response_format: Optional[str] = None
    ) -> Tuple[str, AgentUsage]:
        """
        Enhanced LLM call with better error handling and response parsing.

        Args:
            prompt_parts: List of prompt components (strings or dicts)
            temperature: Sampling temperature
            max_output_tokens: Maximum tokens to generate
            response_format: Expected response format ('json' or None)

        Returns:
            Tuple of (response_text, usage_data)
        """
        start_time = time.time()

        # Call the LLM
        text, usage_raw, duration_ms = call_text_model(
            self.model,
            prompt_parts,
            temperature=temperature,
            max_output_tokens=max_output_tokens
        )

        # Create usage object
        try:
            usage = AgentUsage(
                model=usage_raw.get("model", self.model),
                promptTokens=int(usage_raw.get("promptTokens", 0) or 0),
                completionTokens=int(usage_raw.get("completionTokens", 0) or 0),
                totalTokens=int(usage_raw.get("totalTokens", 0) or 0),
                durationMs=int(duration_ms or 0),
                error=usage_raw.get("error")
            )

            # Estimate cost if possible
            usage.cost = self._estimate_cost(usage)

        except (ValidationError, TypeError) as e:
            logger.error(f"Error creating usage data: {e}")
            usage = AgentUsage(model=self.model, durationMs=duration_ms)

        # Parse JSON response if requested
        if response_format == "json" and text:
            text = self._parse_json_response(text)

        # Log if tracing is enabled
        if self.trace_enabled:
            self._log_llm_call(prompt_parts, text, usage)

        return text, usage

    def _parse_json_response(self, text: str) -> str:
        """Parse and validate JSON response from LLM."""
        try:
            # Remove markdown code blocks if present
            cleaned = text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            # Validate JSON
            json.loads(cleaned.strip())
            return cleaned.strip()

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return text

    def _estimate_cost(self, usage: AgentUsage) -> Optional[float]:
        """Estimate the cost of the LLM call based on token usage."""
        # Rough cost estimates per 1K tokens (adjust based on actual pricing)
        cost_per_1k = {
            "gemini-2.5-flash": {"input": 0.00001, "output": 0.00003},
            "gemini-2.5-pro": {"input": 0.0001, "output": 0.0003},
            "gemini-2.0-flash-exp": {"input": 0.00001, "output": 0.00003}
        }

        model_key = self.model.replace("googleai/", "")
        if model_key in cost_per_1k:
            rates = cost_per_1k[model_key]
            input_cost = (usage.promptTokens / 1000) * rates["input"]
            output_cost = (usage.completionTokens / 1000) * rates["output"]
            return round(input_cost + output_cost, 6)

        return None

    def _log_llm_call(self, prompt_parts: List[Any], response: str, usage: AgentUsage):
        """Log LLM call for tracing."""
        logger.debug(f"LLM Call: model={usage.model}, tokens={usage.totalTokens}, duration={usage.durationMs}ms")

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a registered tool with tracing.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool parameters

        Returns:
            Tool result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found in {self.__class__.__name__}")

        start_time = time.time()

        try:
            # Call the tool
            result = self.tools[tool_name](**kwargs)

            # Record tool call if tracing
            if self.trace_enabled:
                duration_ms = int((time.time() - start_time) * 1000)
                tool_call = ToolCall(
                    name=tool_name,
                    parameters=kwargs,
                    result=result,
                    duration_ms=duration_ms,
                    timestamp=start_time
                )
                self.tool_calls.append(tool_call)
                logger.debug(f"Tool call: {tool_name} completed in {duration_ms}ms")

            return result

        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise

    def run(self, data: BaseModel) -> AgentResult:
        """
        Abstract method to be implemented by concrete agents.
        This is the main entry point for agent execution.

        Args:
            data: Input data for the agent (Pydantic model)

        Returns:
            AgentResult with output data and usage information
        """
        raise NotImplementedError("Subclasses must implement the run method")

    def validate_input(self, data: Any, input_class: Type[BaseModel]) -> BaseModel:
        """
        Validate and parse input data against the expected schema.

        Args:
            data: Raw input data
            input_class: Expected Pydantic model class

        Returns:
            Validated input model instance
        """
        if isinstance(data, input_class):
            return data

        if isinstance(data, dict):
            return input_class(**data)

        if isinstance(data, BaseModel):
            return input_class(**data.model_dump())

        raise ValueError(f"Invalid input type: expected {input_class.__name__}, got {type(data).__name__}")

    def create_result(
        self,
        data: Dict[str, Any],
        usage: AgentUsage,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Create a standardized agent result.

        Args:
            data: Output data
            usage: Usage information
            trace_id: Optional trace identifier
            metadata: Optional metadata

        Returns:
            AgentResult instance
        """
        return AgentResult(
            data=data,
            usage=usage,
            trace_id=trace_id,
            metadata=metadata or {}
        )

    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        Can be overridden by subclasses.
        """
        return f"You are an AI agent: {self.__class__.__name__}"

    def format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """
        Format conversation history for inclusion in prompts.

        Args:
            history: List of conversation messages

        Returns:
            Formatted history string
        """
        if not history:
            return "No previous conversation."

        formatted = []
        for msg in history:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(model={self.model}, tools={list(self.tools.keys())})"