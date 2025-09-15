"""
Agent Card Utilities

Utilities for creating, validating, and managing agent cards.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from .a2a_types import (
    A2A_PROTOCOL_VERSION,
    AgentAuthentication,
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)


# --- Agent Card Templates ---

class AgentCardTemplate:
    """Templates for common agent types."""

    @staticmethod
    def llm_agent(
        name: str,
        version: str,
        description: str,
        url: str,
        model: str = "gemini-2.5-flash",
    ) -> AgentCard:
        """
        Create agent card for LLM-based agent.

        Args:
            name: Agent name
            version: Agent version
            description: Agent description
            url: Agent URL
            model: LLM model used

        Returns:
            Agent card
        """
        return AgentCard(
            name=name,
            version=version,
            description=description,
            url=url,
            skills=[
                AgentSkill(
                    id=f"{name}_conversation",
                    name="Natural Language Conversation",
                    description=f"Engage in natural language conversation using {model}",
                    tags=["llm", "conversation", "nlp"],
                )
            ],
            capabilities=AgentCapabilities(
                supports_streaming=True,
                supports_stateless=True,
                supports_sessions=True,
                max_concurrent_tasks=10,
            ),
            metadata={
                "model": model,
                "agent_type": "llm",
            },
        )

    @staticmethod
    def tool_agent(
        name: str,
        version: str,
        description: str,
        url: str,
        tools: List[Dict[str, Any]],
    ) -> AgentCard:
        """
        Create agent card for tool-based agent.

        Args:
            name: Agent name
            version: Agent version
            description: Agent description
            url: Agent URL
            tools: List of tool definitions

        Returns:
            Agent card
        """
        skills = []
        for tool in tools:
            skill = AgentSkill(
                id=f"{name}_{tool['name']}",
                name=tool.get("display_name", tool["name"]),
                description=tool.get("description", ""),
                tags=["tool"] + tool.get("tags", []),
                input_schema=tool.get("input_schema"),
                output_schema=tool.get("output_schema"),
            )
            skills.append(skill)

        return AgentCard(
            name=name,
            version=version,
            description=description,
            url=url,
            skills=skills,
            capabilities=AgentCapabilities(
                supports_streaming=False,
                supports_stateless=True,
                max_concurrent_tasks=20,
            ),
            metadata={
                "agent_type": "tool",
                "tool_count": len(tools),
            },
        )

    @staticmethod
    def workflow_agent(
        name: str,
        version: str,
        description: str,
        url: str,
        steps: List[str],
    ) -> AgentCard:
        """
        Create agent card for workflow agent.

        Args:
            name: Agent name
            version: Agent version
            description: Agent description
            url: Agent URL
            steps: Workflow steps

        Returns:
            Agent card
        """
        return AgentCard(
            name=name,
            version=version,
            description=description,
            url=url,
            skills=[
                AgentSkill(
                    id=f"{name}_workflow",
                    name="Workflow Execution",
                    description=f"Execute {len(steps)}-step workflow",
                    tags=["workflow", "orchestration"],
                    metadata={
                        "steps": steps,
                    },
                )
            ],
            capabilities=AgentCapabilities(
                supports_streaming=True,
                supports_stateless=False,
                supports_sessions=True,
                max_concurrent_tasks=5,
            ),
            metadata={
                "agent_type": "workflow",
                "step_count": len(steps),
            },
        )


# --- Agent Card Creation ---

def create_agent_card(
    name: str,
    version: str,
    description: str,
    url: str,
    skills: Optional[List[AgentSkill]] = None,
    capabilities: Optional[AgentCapabilities] = None,
    authentication: Optional[AgentAuthentication] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AgentCard:
    """
    Create an agent card.

    Args:
        name: Agent name
        version: Agent version
        description: Agent description
        url: Agent endpoint URL
        skills: Agent skills
        capabilities: Agent capabilities
        authentication: Authentication requirements
        metadata: Additional metadata

    Returns:
        Agent card
    """
    return AgentCard(
        name=name,
        version=version,
        description=description,
        url=url,
        skills=skills or [],
        capabilities=capabilities or AgentCapabilities(),
        authentication=authentication,
        protocol_version=A2A_PROTOCOL_VERSION,
        metadata=metadata or {},
    )


# --- Agent Card Validation ---

def validate_agent_card(agent_card: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate an agent card.

    Args:
        agent_card: Agent card data

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Validate against schema
        card = AgentCard(**agent_card)

        # Additional validation
        if not card.name:
            return False, "Agent name is required"

        if not card.version:
            return False, "Agent version is required"

        if not card.url:
            return False, "Agent URL is required"

        # Check protocol version
        supported_versions = ["0.2.5", "0.2.6", "0.3.0"]
        if card.protocol_version not in supported_versions:
            return False, f"Unsupported protocol version: {card.protocol_version}"

        return True, None

    except ValidationError as e:
        return False, str(e)

    except Exception as e:
        return False, f"Validation error: {e}"


# --- Agent Card Merging ---

def merge_agent_cards(
    base_card: AgentCard,
    override_card: Dict[str, Any],
) -> AgentCard:
    """
    Merge two agent cards.

    Args:
        base_card: Base agent card
        override_card: Override values

    Returns:
        Merged agent card
    """
    # Convert base to dict
    base_dict = base_card.model_dump()

    # Merge fields
    for key, value in override_card.items():
        if key == "skills":
            # Merge skills by ID
            base_skills = {s["id"]: s for s in base_dict.get("skills", [])}
            for skill in value:
                base_skills[skill["id"]] = skill
            base_dict["skills"] = list(base_skills.values())

        elif key == "capabilities" and isinstance(value, dict):
            # Merge capabilities
            base_dict.setdefault("capabilities", {}).update(value)

        elif key == "metadata" and isinstance(value, dict):
            # Merge metadata
            base_dict.setdefault("metadata", {}).update(value)

        else:
            # Override value
            base_dict[key] = value

    return AgentCard(**base_dict)


# --- Agent Card I/O ---

def load_agent_card(file_path: Path) -> AgentCard:
    """
    Load agent card from file.

    Args:
        file_path: Path to agent card file

    Returns:
        Agent card

    Raises:
        ValueError: If file is invalid
    """
    if not file_path.exists():
        raise ValueError(f"Agent card file not found: {file_path}")

    with open(file_path, "r") as f:
        data = json.load(f)

    # Validate
    is_valid, error = validate_agent_card(data)
    if not is_valid:
        raise ValueError(f"Invalid agent card: {error}")

    return AgentCard(**data)


def save_agent_card(agent_card: AgentCard, file_path: Path):
    """
    Save agent card to file.

    Args:
        agent_card: Agent card to save
        file_path: Output file path
    """
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as JSON
    with open(file_path, "w") as f:
        json.dump(
            agent_card.model_dump(),
            f,
            indent=2,
            default=str,  # Handle non-JSON types
        )


# --- Agent Card Discovery ---

def discover_agent_cards(directory: Path) -> List[AgentCard]:
    """
    Discover agent cards in a directory.

    Args:
        directory: Directory to search

    Returns:
        List of discovered agent cards
    """
    cards = []

    # Search for agent.json files
    for card_file in directory.rglob("agent.json"):
        try:
            card = load_agent_card(card_file)
            cards.append(card)
        except Exception as e:
            # Log but don't fail
            print(f"Failed to load {card_file}: {e}")

    # Search for .well-known/agent.json
    well_known = directory / ".well-known" / "agent.json"
    if well_known.exists():
        try:
            card = load_agent_card(well_known)
            cards.append(card)
        except Exception as e:
            print(f"Failed to load {well_known}: {e}")

    return cards


# --- Agent Card Generation ---

def generate_agent_card_from_code(
    agent_class: type,
    url: str,
    version: str = "1.0.0",
) -> AgentCard:
    """
    Generate agent card from agent class.

    Args:
        agent_class: Agent class
        url: Agent URL
        version: Agent version

    Returns:
        Generated agent card
    """
    # Extract metadata from class
    name = getattr(agent_class, "name", agent_class.__name__)
    description = getattr(
        agent_class,
        "description",
        agent_class.__doc__ or "No description"
    )

    # Extract skills from methods
    skills = []
    for method_name in dir(agent_class):
        if method_name.startswith("_"):
            continue

        method = getattr(agent_class, method_name)
        if not callable(method):
            continue

        # Check for skill decorator or annotation
        if hasattr(method, "_is_skill"):
            skill = AgentSkill(
                id=f"{name}_{method_name}",
                name=getattr(method, "_skill_name", method_name),
                description=getattr(
                    method,
                    "_skill_description",
                    method.__doc__ or ""
                ),
                tags=getattr(method, "_skill_tags", []),
            )
            skills.append(skill)

    # Extract capabilities
    capabilities = AgentCapabilities(
        supports_streaming=getattr(agent_class, "supports_streaming", False),
        supports_stateless=getattr(agent_class, "supports_stateless", True),
        supports_sessions=getattr(agent_class, "supports_sessions", False),
        max_concurrent_tasks=getattr(agent_class, "max_concurrent_tasks", 10),
    )

    return AgentCard(
        name=name,
        version=version,
        description=description,
        url=url,
        skills=skills,
        capabilities=capabilities,
    )