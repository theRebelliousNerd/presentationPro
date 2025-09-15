"""
Base classes and utilities for ADK agents.
This module contains minimal executable scaffolding shared by all agents.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ValidationError

from app.llm import call_text_model


class AgentUsage(BaseModel):
    """A Pydantic model for tracking agent usage."""
    model: str
    promptTokens: int = 0
    completionTokens: int = 0
    durationMs: int = 0


class AgentResult(BaseModel):
    """A Pydantic model for the result of an agent's execution."""
    data: Dict[str, Any]
    usage: AgentUsage


class BaseAgent:
    """A base class for all agents, providing common functionality."""

    def __init__(self, model: Optional[str] = None) -> None:
        """Initializes the agent with a default model."""
        self.model = model or "googleai/gemini-2.5-flash"

    def llm(self, prompt_parts: List[Dict[str, str]]) -> Tuple[str, AgentUsage]:
        """
        Calls the language model and returns the response and usage data.

        Args:
            prompt_parts: A list of dictionaries representing the prompt.

        Returns:
            A tuple containing the response text and usage data.
        """
        text, usage_raw, duration_ms = call_text_model(self.model, prompt_parts)
        try:
            usage = AgentUsage(
                model=usage_raw.get("model", self.model),
                promptTokens=int(usage_raw.get("promptTokens", 0) or 0),
                completionTokens=int(usage_raw.get("completionTokens", 0) or 0),
                durationMs=int(duration_ms or usage_raw.get("durationMs", 0) or 0),
            )
        except (ValidationError, TypeError) as e:
            print(f"Error validating usage data: {e}")
            usage = AgentUsage(model=self.model) # Return a default usage object on error
        return text, usage