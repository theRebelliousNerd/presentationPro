"""
PresentationPro A2A Orchestrator Service

Main orchestrator that coordinates multi-agent presentation generation
using the A2A protocol for all agent communication.
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Comment out missing imports for now - these modules need to be created
# from workflow_engine import WorkflowEngine, WorkflowState
# from agent_discovery import AgentDiscovery, AgentRegistry
# from session_manager import SessionManager, PresentationSession
# from api_routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PORT = int(os.environ.get("ORCHESTRATOR_PORT", "8080"))
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")

# Agent service URLs (Docker network names)
AGENT_URLS = {
    "clarifier": os.environ.get("CLARIFIER_URL", "http://clarifier:10001"),
    "outline": os.environ.get("OUTLINE_URL", "http://outline:10002"),
    "slide_writer": os.environ.get("SLIDE_WRITER_URL", "http://slide-writer:10003"),
    "critic": os.environ.get("CRITIC_URL", "http://critic:10004"),
    "notes_polisher": os.environ.get("NOTES_POLISHER_URL", "http://notes-polisher:10005"),
    "design": os.environ.get("DESIGN_URL", "http://design:10006"),
    "script_writer": os.environ.get("SCRIPT_WRITER_URL", "http://script-writer:10007"),
    "research": os.environ.get("RESEARCH_URL", "http://research:10008")
}


class OrchestratorService:
    """
    Main orchestrator service that coordinates all presentation generation workflows.
    """

    def __init__(self):
        """Initialize the orchestrator service."""
        self.app = self._create_app()
        self.discovery = AgentDiscovery(AGENT_URLS)
        self.registry = AgentRegistry()
        self.session_manager = SessionManager()
        self.workflow_engine = WorkflowEngine(self.registry, self.session_manager)
        self.startup_time = datetime.utcnow()
        self.request_count = 0
        self.error_count = 0

    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        app = FastAPI(
            title="PresentationPro A2A Orchestrator",
            version="2.0.0",
            description="Multi-agent orchestration service using A2A protocol",
            docs_url="/docs" if ENVIRONMENT != "production" else None,
            redoc_url="/redoc" if ENVIRONMENT != "production" else None
        )

        # Configure CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        return app

    async def initialize(self):
        """Initialize the orchestrator by discovering all agents."""
        logger.info("Initializing PresentationPro Orchestrator...")

        # Discover all agents
        discovered = await self.discovery.discover_all()

        # Register discovered agents
        for agent_name, agent_card in discovered.items():
            self.registry.register(agent_name, agent_card)
            logger.info(f"Registered agent: {agent_name} v{agent_card.version}")

        # Initialize workflow engine
        await self.workflow_engine.initialize()

        # Start health monitoring
        asyncio.create_task(self._monitor_agents())

        logger.info(f"Orchestrator initialized with {len(discovered)} agents")

    async def _monitor_agents(self):
        """Continuously monitor agent health."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                # Check health of all registered agents
                for agent_name in self.registry.list_agents():
                    try:
                        healthy = await self.discovery.check_health(agent_name)
                        self.registry.update_health(agent_name, healthy)

                        if not healthy:
                            logger.warning(f"Agent {agent_name} is unhealthy")

                    except Exception as e:
                        logger.error(f"Health check failed for {agent_name}: {e}")
                        self.registry.update_health(agent_name, False)

            except Exception as e:
                logger.error(f"Agent monitoring error: {e}")

    def setup_routes(self):
        """Setup API routes."""
        # Include API router
        self.app.include_router(api_router, prefix="/v1")

        # Health check
        @self.app.get("/health")
        async def health_check():
            """Service health check."""
            uptime = (datetime.utcnow() - self.startup_time).total_seconds()
            agents_status = self.registry.get_health_status()

            # Determine overall health
            healthy_agents = sum(1 for s in agents_status.values() if s)
            total_agents = len(agents_status)
            health_score = healthy_agents / total_agents if total_agents > 0 else 0

            return {
                "status": "healthy" if health_score > 0.5 else "degraded",
                "version": "2.0.0",
                "uptime": uptime,
                "requests": self.request_count,
                "errors": self.error_count,
                "agents": {
                    "total": total_agents,
                    "healthy": healthy_agents,
                    "status": agents_status
                },
                "sessions": {
                    "active": self.session_manager.count_active(),
                    "total": self.session_manager.count_total()
                }
            }

        # Agent discovery endpoint
        @self.app.get("/v1/agents")
        async def list_agents():
            """List all discovered agents and their capabilities."""
            agents = []

            for agent_name in self.registry.list_agents():
                agent_card = self.registry.get_agent(agent_name)
                if agent_card:
                    agents.append({
                        "name": agent_card.name,
                        "version": agent_card.version,
                        "description": agent_card.description,
                        "url": str(agent_card.url),
                        "healthy": self.registry.is_healthy(agent_name),
                        "capabilities": agent_card.capabilities.model_dump(),
                        "skills": [
                            {"id": s.id, "name": s.name, "description": s.description}
                            for s in agent_card.skills
                        ]
                    })

            return {"agents": agents}

        # Clarification endpoint
        @self.app.post("/v1/clarify")
        async def clarify(request: Dict[str, Any]):
            """Execute clarification workflow."""
            self.request_count += 1

            try:
                # Create or get session
                session_id = request.get("session_id")
                if not session_id:
                    session = self.session_manager.create_session()
                    session_id = session.id
                else:
                    session = self.session_manager.get_session(session_id)
                    if not session:
                        session = self.session_manager.create_session(session_id)

                # Execute clarification workflow
                result = await self.workflow_engine.clarify(
                    session_id=session_id,
                    history=request.get("history", []),
                    initial_input=request.get("initialInput", {}),
                    new_files=request.get("newFiles")
                )

                return {
                    "refinedGoals": result.get("response", ""),
                    "finished": result.get("finished", False),
                    "session_id": session_id,
                    "usage": result.get("usage", {})
                }

            except Exception as e:
                self.error_count += 1
                logger.error(f"Clarification failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Outline generation endpoint
        @self.app.post("/v1/outline")
        async def generate_outline(request: Dict[str, Any]):
            """Generate presentation outline."""
            self.request_count += 1

            try:
                session_id = request.get("session_id")
                if not session_id:
                    raise HTTPException(status_code=400, detail="session_id required")

                session = self.session_manager.get_session(session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")

                # Execute outline generation
                result = await self.workflow_engine.generate_outline(
                    session_id=session_id,
                    refined_goals=request.get("refinedGoals", ""),
                    assets=request.get("assets")
                )

                return {
                    "outline": result.get("outline", {}),
                    "session_id": session_id,
                    "usage": result.get("usage", {})
                }

            except HTTPException:
                raise
            except Exception as e:
                self.error_count += 1
                logger.error(f"Outline generation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Slide generation endpoint
        @self.app.post("/v1/slide/write")
        async def generate_slide(request: Dict[str, Any]):
            """Generate a complete slide with all enhancements."""
            self.request_count += 1

            try:
                session_id = request.get("session_id")
                if not session_id:
                    raise HTTPException(status_code=400, detail="session_id required")

                session = self.session_manager.get_session(session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")

                # Execute slide generation pipeline
                result = await self.workflow_engine.generate_slide(
                    session_id=session_id,
                    slide_number=request.get("slideNumber", 1),
                    outline=request.get("outline", {}),
                    refined_goals=request.get("refinedGoals", "")
                )

                return {
                    "slides": [result.get("slide", {})],
                    "session_id": session_id,
                    "usage": result.get("usage", {})
                }

            except HTTPException:
                raise
            except Exception as e:
                self.error_count += 1
                logger.error(f"Slide generation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Research endpoint
        @self.app.post("/v1/research/backgrounds")
        async def research_backgrounds(request: Dict[str, Any]):
            """Execute research workflow."""
            self.request_count += 1

            try:
                session_id = request.get("session_id")
                if not session_id:
                    session = self.session_manager.create_session()
                    session_id = session.id
                else:
                    session = self.session_manager.get_session(session_id)
                    if not session:
                        session = self.session_manager.create_session(session_id)

                # Execute research
                result = await self.workflow_engine.research(
                    session_id=session_id,
                    topic=request.get("topic", ""),
                    context=request.get("context", {})
                )

                return {
                    "rules": result.get("rules", []),
                    "session_id": session_id,
                    "usage": result.get("usage", {})
                }

            except Exception as e:
                self.error_count += 1
                logger.error(f"Research failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Session management endpoints
        @self.app.get("/v1/sessions/{session_id}")
        async def get_session(session_id: str):
            """Get session details."""
            session = self.session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            return session.to_dict()

        @self.app.get("/v1/sessions")
        async def list_sessions():
            """List all sessions."""
            sessions = self.session_manager.list_sessions()
            return {"sessions": sessions}

        @self.app.delete("/v1/sessions/{session_id}")
        async def delete_session(session_id: str):
            """Delete a session."""
            if self.session_manager.delete_session(session_id):
                return {"status": "deleted"}
            else:
                raise HTTPException(status_code=404, detail="Session not found")

        # Presentation complete endpoint
        @self.app.post("/v1/presentations/{session_id}/complete")
        async def complete_presentation(session_id: str):
            """Mark presentation as complete and trigger final assembly."""
            session = self.session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            try:
                # Execute script generation if needed
                if "script_writer" in self.registry.list_agents():
                    result = await self.workflow_engine.generate_script(
                        session_id=session_id,
                        presentation_data=session.get_presentation_data()
                    )
                    session.add_result("script", result)

                # Mark session as complete
                session.complete()

                return {
                    "status": "complete",
                    "session_id": session_id,
                    "presentation": session.get_presentation_data()
                }

            except Exception as e:
                logger.error(f"Presentation completion failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("Shutting down orchestrator...")

        # Close all active sessions
        active_sessions = self.session_manager.get_active_sessions()
        for session_id in active_sessions:
            session = self.session_manager.get_session(session_id)
            if session:
                session.error("Service shutting down")

        # Close agent connections
        await self.discovery.close()

        logger.info("Orchestrator shutdown complete")


# Create global orchestrator instance
orchestrator = OrchestratorService()

# Setup FastAPI app
app = orchestrator.app

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup."""
    await orchestrator.initialize()
    orchestrator.setup_routes()
    logger.info(f"Orchestrator started on port {PORT}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    await orchestrator.shutdown()


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting PresentationPro Orchestrator on port {PORT}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=ENVIRONMENT == "development",
        log_level="info"
    )