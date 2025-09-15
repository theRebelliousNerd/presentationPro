"""
Protocol Definitions

Type definitions for A2A and MCP protocols.
"""

from .a2a_types import (
    A2ARequest,
    A2AResponse,
    A2AMethod,
    A2AError,
    TaskRequest,
    TaskResponse,
    TaskStatus,
    AgentCard,
    AgentSkill,
)
from .mcp_types import (
    MCPRequest,
    MCPResponse,
    MCPTool,
    MCPResource,
    MCPPrompt,
)
from .agent_cards import (
    create_agent_card,
    validate_agent_card,
    merge_agent_cards,
    AgentCardTemplate,
)

__all__ = [
    # A2A types
    "A2ARequest",
    "A2AResponse",
    "A2AMethod",
    "A2AError",
    "TaskRequest",
    "TaskResponse",
    "TaskStatus",
    "AgentCard",
    "AgentSkill",
    # MCP types
    "MCPRequest",
    "MCPResponse",
    "MCPTool",
    "MCPResource",
    "MCPPrompt",
    # Agent cards
    "create_agent_card",
    "validate_agent_card",
    "merge_agent_cards",
    "AgentCardTemplate",
]