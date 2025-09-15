"""
ADK Agent Base Classes

Provides the core Agent classes compatible with Google ADK patterns.
These are simplified implementations that work with the existing wrapper architecture.
"""

from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


@dataclass
class Agent:
    """
    Base Agent class following ADK patterns.

    This is a simplified implementation that provides the interface
    expected by ADK agents while working with our wrapper system.
    """
    name: str
    model: str = "gemini-2.0-flash-exp"
    description: str = ""
    instruction: str = ""
    tools: List[Any] = field(default_factory=list)
    sub_agents: List['Agent'] = field(default_factory=list)

    def __post_init__(self):
        """Initialize the agent after dataclass initialization."""
        logger.info(f"Initialized Agent: {self.name}")

    def run(self, input_data: Any) -> Any:
        """
        Run the agent with the given input.

        This is a placeholder that would normally orchestrate the agent's execution.
        In our wrapper system, the actual logic is in the wrapper classes.
        """
        logger.debug(f"Agent {self.name} run() called with: {input_data}")
        return {"status": "success", "agent": self.name}

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation."""
        return {
            "name": self.name,
            "model": self.model,
            "description": self.description,
            "instruction": self.instruction,
            "tools": [str(tool) for tool in self.tools],
            "sub_agents": [agent.name for agent in self.sub_agents]
        }


@dataclass
class LlmAgent(Agent):
    """
    LLM-based Agent class for language model interactions.

    Extends the base Agent with LLM-specific capabilities.
    """
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: Optional[str] = None

    def __post_init__(self):
        """Initialize the LLM agent."""
        super().__post_init__()
        if self.system_prompt is None:
            self.system_prompt = self.instruction

    def generate(self, prompt: str) -> str:
        """
        Generate a response using the LLM.

        In our wrapper system, this would delegate to the actual LLM call.
        """
        logger.debug(f"LlmAgent {self.name} generating response for prompt")
        # Placeholder - actual implementation in wrappers
        return f"Response from {self.name}"


class BaseAgent:
    """
    Alternative base class for custom agent implementations.

    This provides more flexibility for agents that need custom control flow.
    """

    def __init__(self, name: str, description: str = "", **kwargs):
        """Initialize the base agent."""
        self.name = name
        self.description = description
        self.config = kwargs
        logger.info(f"Initialized BaseAgent: {self.name}")

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's logic asynchronously.

        Args:
            context: Execution context with input data

        Returns:
            Dict with execution results
        """
        logger.debug(f"BaseAgent {self.name} executing")
        # Override in subclasses
        return {"status": "success", "agent": self.name}

    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data before execution.

        Args:
            input_data: Input to validate

        Returns:
            True if valid, False otherwise
        """
        return True

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"BaseAgent(name='{self.name}', description='{self.description}')"


# Agent registry for discovery
_agent_registry: Dict[str, Agent] = {}


def register_agent(agent: Agent) -> None:
    """
    Register an agent for discovery.

    Args:
        agent: Agent instance to register
    """
    _agent_registry[agent.name] = agent
    logger.info(f"Registered agent: {agent.name}")


def get_agent(name: str) -> Optional[Agent]:
    """
    Get a registered agent by name.

    Args:
        name: Name of the agent

    Returns:
        Agent instance or None if not found
    """
    return _agent_registry.get(name)


def list_agents() -> List[str]:
    """
    List all registered agent names.

    Returns:
        List of agent names
    """
    return list(_agent_registry.keys())