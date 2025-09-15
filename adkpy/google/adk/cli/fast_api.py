"""
Google ADK FastAPI integration module.

Provides FastAPI app creation for ADK agents.
"""

from typing import Optional, List, Any
from fastapi import FastAPI
import os
import logging

logger = logging.getLogger(__name__)


def get_fast_api_app(
    agent_dir: Optional[str] = "./agents",
    title: str = "ADK Agent API",
    version: str = "1.0.0"
) -> FastAPI:
    """
    Create a FastAPI application for ADK agents.

    Args:
        agent_dir: Directory containing agent definitions
        title: API title
        version: API version

    Returns:
        FastAPI application instance
    """
    app = FastAPI(title=title, version=version)

    # Discover and load agents from the specified directory
    if os.path.exists(agent_dir):
        logger.info(f"Loading agents from {agent_dir}")
        # Agent loading would happen here in full implementation

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "service": title,
            "version": version,
            "status": "running"
        }

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.get("/agents")
    async def list_agents():
        """List available agents."""
        from adk.agents import list_agents
        return {"agents": list_agents()}

    return app