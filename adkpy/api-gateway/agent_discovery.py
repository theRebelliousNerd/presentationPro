"""
Agent Discovery and Registry

Handles dynamic discovery of A2A agents via their agent cards,
maintains a registry of available agents, and monitors their health.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field, HttpUrl


logger = logging.getLogger(__name__)


class AgentSkill(BaseModel):
    """Agent skill definition."""
    id: str
    name: str
    description: str
    inputSchema: Optional[Dict[str, Any]] = None
    outputSchema: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)


class AgentCapabilities(BaseModel):
    """Agent capabilities declaration."""
    supportsStreaming: bool = False
    supportsStateless: bool = True
    maxConcurrentTasks: int = 10
    timeout: int = 300


class AgentCard(BaseModel):
    """Agent metadata and capabilities."""
    name: str
    version: str
    description: str
    url: HttpUrl
    skills: List[AgentSkill] = Field(default_factory=list)
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    protocolVersion: str = "0.2.6"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentHealth(BaseModel):
    """Agent health status."""
    agent_name: str
    healthy: bool
    last_check: datetime
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    consecutive_failures: int = 0


class AgentRegistry:
    """
    Registry of discovered agents with health tracking.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self.agents: Dict[str, AgentCard] = {}
        self.health: Dict[str, AgentHealth] = {}
        self.skills_index: Dict[str, List[str]] = {}  # skill_id -> [agent_names]

    def register(self, agent_name: str, agent_card: AgentCard):
        """
        Register an agent.

        Args:
            agent_name: Unique agent identifier
            agent_card: Agent metadata
        """
        self.agents[agent_name] = agent_card

        # Index skills for quick lookup
        for skill in agent_card.skills:
            if skill.id not in self.skills_index:
                self.skills_index[skill.id] = []
            if agent_name not in self.skills_index[skill.id]:
                self.skills_index[skill.id].append(agent_name)

        # Initialize health tracking
        self.health[agent_name] = AgentHealth(
            agent_name=agent_name,
            healthy=True,
            last_check=datetime.utcnow()
        )

        logger.info(f"Registered agent: {agent_name} with {len(agent_card.skills)} skills")

    def get_agent(self, agent_name: str) -> Optional[AgentCard]:
        """Get agent card by name."""
        return self.agents.get(agent_name)

    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self.agents.keys())

    def find_agents_by_skill(self, skill_id: str) -> List[str]:
        """
        Find agents that provide a specific skill.

        Args:
            skill_id: Skill identifier

        Returns:
            List of agent names
        """
        return self.skills_index.get(skill_id, [])

    def is_healthy(self, agent_name: str) -> bool:
        """Check if an agent is healthy."""
        health = self.health.get(agent_name)
        return health.healthy if health else False

    def update_health(self, agent_name: str, healthy: bool, response_time_ms: Optional[float] = None, error: Optional[str] = None):
        """
        Update agent health status.

        Args:
            agent_name: Agent identifier
            healthy: Health status
            response_time_ms: Response time in milliseconds
            error: Error message if unhealthy
        """
        if agent_name not in self.health:
            self.health[agent_name] = AgentHealth(
                agent_name=agent_name,
                healthy=healthy,
                last_check=datetime.utcnow()
            )
        else:
            health = self.health[agent_name]
            health.healthy = healthy
            health.last_check = datetime.utcnow()
            health.response_time_ms = response_time_ms
            health.error = error

            if not healthy:
                health.consecutive_failures += 1
            else:
                health.consecutive_failures = 0

    def get_health_status(self) -> Dict[str, bool]:
        """Get health status of all agents."""
        return {
            agent_name: health.healthy
            for agent_name, health in self.health.items()
        }

    def get_healthy_agents(self) -> List[str]:
        """Get list of healthy agents."""
        return [
            agent_name
            for agent_name, health in self.health.items()
            if health.healthy
        ]

    def remove_agent(self, agent_name: str):
        """
        Remove an agent from the registry.

        Args:
            agent_name: Agent identifier
        """
        if agent_name in self.agents:
            # Remove from skills index
            agent_card = self.agents[agent_name]
            for skill in agent_card.skills:
                if skill.id in self.skills_index:
                    self.skills_index[skill.id] = [
                        name for name in self.skills_index[skill.id]
                        if name != agent_name
                    ]

            # Remove agent
            del self.agents[agent_name]
            if agent_name in self.health:
                del self.health[agent_name]

            logger.info(f"Removed agent: {agent_name}")


class AgentDiscovery:
    """
    Discovers A2A agents via their well-known agent cards.
    """

    def __init__(self, agent_urls: Dict[str, str], timeout: int = 10):
        """
        Initialize agent discovery.

        Args:
            agent_urls: Mapping of agent names to base URLs
            timeout: Discovery timeout in seconds
        """
        self.agent_urls = agent_urls
        self.timeout = timeout
        self.http_client = httpx.AsyncClient(timeout=timeout)

    async def discover_agent(self, agent_name: str, agent_url: str) -> Optional[AgentCard]:
        """
        Discover a single agent.

        Args:
            agent_name: Agent identifier
            agent_url: Agent base URL

        Returns:
            Agent card if successful, None otherwise
        """
        try:
            # Fetch agent card from well-known endpoint
            card_url = urljoin(agent_url, "/.well-known/agent.json")

            logger.info(f"Discovering agent {agent_name} at {card_url}")

            response = await self.http_client.get(card_url)
            response.raise_for_status()

            # Parse agent card
            card_data = response.json()

            # Override URL with the one we're actually using
            card_data["url"] = agent_url

            agent_card = AgentCard(**card_data)

            logger.info(f"Discovered agent: {agent_card.name} v{agent_card.version}")
            return agent_card

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error discovering {agent_name}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Network error discovering {agent_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error discovering {agent_name}: {e}")
            return None

    async def discover_all(self) -> Dict[str, AgentCard]:
        """
        Discover all configured agents.

        Returns:
            Dictionary of agent names to agent cards
        """
        discovered = {}

        # Create discovery tasks
        tasks = []
        for agent_name, agent_url in self.agent_urls.items():
            task = asyncio.create_task(
                self.discover_agent(agent_name, agent_url)
            )
            tasks.append((agent_name, task))

        # Wait for all discoveries
        for agent_name, task in tasks:
            try:
                agent_card = await task
                if agent_card:
                    discovered[agent_name] = agent_card
                else:
                    logger.warning(f"Failed to discover agent: {agent_name}")
            except Exception as e:
                logger.error(f"Discovery error for {agent_name}: {e}")

        logger.info(f"Discovered {len(discovered)} out of {len(self.agent_urls)} agents")
        return discovered

    async def check_health(self, agent_name: str) -> bool:
        """
        Check health of a specific agent.

        Args:
            agent_name: Agent identifier

        Returns:
            True if healthy, False otherwise
        """
        agent_url = self.agent_urls.get(agent_name)
        if not agent_url:
            return False

        try:
            health_url = urljoin(agent_url, "/health")

            start_time = datetime.utcnow()
            response = await self.http_client.get(health_url)
            response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            response.raise_for_status()

            health_data = response.json()

            # Check if status indicates health
            status = health_data.get("status", "").lower()
            healthy = status in ["healthy", "ok", "ready"]

            logger.debug(f"Agent {agent_name} health: {status} ({response_time_ms:.2f}ms)")
            return healthy

        except Exception as e:
            logger.warning(f"Health check failed for {agent_name}: {e}")
            return False

    async def monitor_health(self, registry: AgentRegistry, interval: int = 30):
        """
        Continuously monitor agent health.

        Args:
            registry: Agent registry to update
            interval: Check interval in seconds
        """
        logger.info(f"Starting health monitoring with {interval}s interval")

        while True:
            try:
                await asyncio.sleep(interval)

                # Check health of all registered agents
                for agent_name in registry.list_agents():
                    try:
                        start_time = datetime.utcnow()
                        healthy = await self.check_health(agent_name)
                        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                        registry.update_health(
                            agent_name,
                            healthy,
                            response_time_ms if healthy else None,
                            None if healthy else "Health check failed"
                        )

                        if not healthy:
                            health = registry.health.get(agent_name)
                            if health and health.consecutive_failures >= 3:
                                logger.error(f"Agent {agent_name} has failed {health.consecutive_failures} consecutive health checks")

                    except Exception as e:
                        logger.error(f"Error checking health of {agent_name}: {e}")
                        registry.update_health(agent_name, False, error=str(e))

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")

    async def close(self):
        """Clean up resources."""
        await self.http_client.aclose()


class AgentResolver:
    """
    Resolves agent requirements to specific agent instances.
    """

    def __init__(self, registry: AgentRegistry):
        """
        Initialize agent resolver.

        Args:
            registry: Agent registry
        """
        self.registry = registry

    def resolve_by_skill(self, skill_id: str, prefer_healthy: bool = True) -> Optional[str]:
        """
        Resolve an agent that provides a specific skill.

        Args:
            skill_id: Required skill
            prefer_healthy: Prefer healthy agents

        Returns:
            Agent name if found, None otherwise
        """
        candidates = self.registry.find_agents_by_skill(skill_id)

        if not candidates:
            return None

        if prefer_healthy:
            # Filter healthy agents
            healthy_candidates = [
                name for name in candidates
                if self.registry.is_healthy(name)
            ]
            if healthy_candidates:
                candidates = healthy_candidates

        # Return first candidate (could implement load balancing here)
        return candidates[0] if candidates else None

    def resolve_best_agent(
        self,
        skill_id: str,
        criteria: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Resolve the best agent for a skill based on criteria.

        Args:
            skill_id: Required skill
            criteria: Selection criteria (e.g., version, capabilities)

        Returns:
            Best agent name if found
        """
        candidates = self.registry.find_agents_by_skill(skill_id)

        if not candidates:
            return None

        # Score candidates
        scored = []
        for agent_name in candidates:
            score = 0

            # Health score
            if self.registry.is_healthy(agent_name):
                score += 100

            # Response time score
            health = self.registry.health.get(agent_name)
            if health and health.response_time_ms:
                # Lower response time is better
                score += max(0, 100 - health.response_time_ms / 10)

            # Version score (if criteria specified)
            if criteria and "min_version" in criteria:
                agent_card = self.registry.get_agent(agent_name)
                if agent_card and agent_card.version >= criteria["min_version"]:
                    score += 50

            scored.append((agent_name, score))

        # Sort by score (highest first)
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[0][0] if scored else None