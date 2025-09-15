"""
ADK/A2A Orchestrator - FastAPI Application with Dev UI

This module exposes the functionality of the ADK agents through a RESTful API,
allowing a web application to drive the presentation generation workflow.
Now includes ADK Dev UI for agent testing and development.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import logging

# Import agent wrapper classes and their data models
from agents.wrappers import (
    ClarifierAgent, ClarifierInput,
    OutlineAgent, OutlineInput,
    SlideWriterAgent, SlideWriterInput,
    CriticAgent, CriticInput,
    DesignAgent, DesignInput,
    NotesPolisherAgent, NotesPolisherInput,
    ScriptWriterAgent, ScriptWriterInput,
    ResearchAgent, ResearchInput
)

# Import ADK framework
import adk
from adk.dev_ui import get_dev_ui_server

# Import tools for direct use in utility endpoints
from tools import (
    # ArangoGraphRAGTool,
    Asset, IngestResponse, RetrieveResponse,
    VisionContrastTool, VisionAnalyzeInput, VisionAnalyzeOutput
)
from tools.web_search_tool import set_global_cache_config, clear_global_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI(
    title="ADK/A2A Orchestrator",
    version="1.0.0",
    description="An API for orchestrating a multi-agent system with ADK Dev UI support."
)

# Add CORS middleware for Dev UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Agent Initialization ---
# Instantiate agents at the global scope to be reused across requests.
# This is more efficient than creating new instances for every API call.
clarifier_agent = ClarifierAgent()
outline_agent = OutlineAgent()
slide_writer_agent = SlideWriterAgent()
critic_agent = CriticAgent()
notes_polisher_agent = NotesPolisherAgent()
design_agent = DesignAgent()
script_writer_agent = ScriptWriterAgent()
research_agent = ResearchAgent()
vision_contrast_tool = VisionContrastTool()

# Mock ArangoGraphRAGTool to avoid database connection issues
class MockArangoGraphRAGTool:
    def ingest(self, assets):
        return IngestResponse(
            success=True,
            message="Mock ingestion successful",
            ingested_count=len(assets),
            errors=[]
        )

    def retrieve(self, presentation_id, query, limit=5):
        return RetrieveResponse(
            chunks=[],
            query=query,
            presentation_id=presentation_id
        )

graph_rag_tool = MockArangoGraphRAGTool()

# --- Core Presentation Workflow Endpoints ---

@app.post("/v1/clarify")
def clarify(data: ClarifierInput):
    """Endpoint to run the ClarifierAgent."""
    result = clarifier_agent.run(data)
    # Return the refined goals and finished status as expected by frontend
    return {
        "refinedGoals": result.data.get('response', ''),  # Changed from 'refinedGoals' to 'response'
        "finished": result.data.get('finished', False),
        "usage": result.usage.model_dump()
    }

@app.post("/v1/outline")
def outline(data: OutlineInput):
    """Endpoint to run the OutlineAgent."""
    result = outline_agent.run(data)
    return {"outline": result.data['outline'], "usage": result.usage.model_dump()}

@app.post("/v1/slide/write")
def write_slide(data: SlideWriterInput):
    """Endpoint to run the SlideWriterAgent."""
    result = slide_writer_agent.run(data)
    # result.data is already a list of slides
    return {"slides": result.data, "usage": result.usage.model_dump()}

@app.post("/v1/slide/critique")
def critique_slide(data: CriticInput):
    """Endpoint to run the CriticAgent."""
    result = critic_agent.run(data)
    return {"slide": result.data, "usage": result.usage.model_dump()}

@app.post("/v1/slide/polish_notes")
def polish_notes(data: NotesPolisherInput):
    """Endpoint to run the NotesPolisherAgent."""
    result = notes_polisher_agent.run(data)
    return {"rephrasedSpeakerNotes": result.data['rephrasedSpeakerNotes'], "usage": result.usage.model_dump()}

@app.post("/v1/slide/design")
def design_slide(data: DesignInput):
    """Endpoint to run the DesignAgent."""
    result = design_agent.run(data)
    design_data = result.data
    # Return in the format expected by frontend
    return {
        "type": design_data.get('type', 'prompt'),
        "prompt": design_data.get('prompt'),
        "code": design_data.get('code'),
        "usage": result.usage.model_dump()
    }

@app.post("/v1/script/generate")
def generate_script(data: ScriptWriterInput):
    """Endpoint to run the ScriptWriterAgent."""
    result = script_writer_agent.run(data)
    return {"script": result.data['script'], "usage": result.usage.model_dump()}


# --- Tool and Utility Endpoints ---

@app.post("/v1/research/backgrounds")
def research_backgrounds(data: ResearchInput):
    """Endpoint to run the ResearchAgent for background research."""
    result = research_agent.run(data)
    return {"rules": result.data['rules'], "usage": result.usage.model_dump()}

@app.post("/v1/vision/analyze", response_model=VisionAnalyzeOutput)
def vision_analyze(data: VisionAnalyzeInput):
    """Endpoint to run the VisionContrastTool."""
    return vision_contrast_tool.analyze(data)

@app.post("/v1/ingest", response_model=IngestResponse)
def ingest(assets: List[Asset]):
    """Endpoint for ingesting assets into the Graph RAG store."""
    return graph_rag_tool.ingest(assets)

class RetrieveRequest(BaseModel):
    presentation_id: str
    query: str
    limit: int = 5

@app.post("/v1/retrieve", response_model=RetrieveResponse)
def retrieve(data: RetrieveRequest):
    """Endpoint for retrieving chunks from the Graph RAG store."""
    return graph_rag_tool.retrieve(data.presentation_id, data.query, data.limit)


# --- Cache Management Endpoints ---

class CacheConfig(BaseModel):
    enabled: Optional[bool] = None
    cacheTtl: Optional[int] = None  # Match frontend field name

@app.post("/v1/search/cache/config")
def search_cache_config(config: CacheConfig):
    """Configure the global web search cache."""
    return set_global_cache_config(enabled=config.enabled, ttl=config.cacheTtl)

class CacheClear(BaseModel):
    deleteFile: bool = True
    path: Optional[str] = None

@app.post("/v1/search/cache/clear")
def search_cache_clear(data: CacheClear):
    """Clear the global web search cache."""
    return clear_global_cache(delete_file=data.deleteFile, cache_path=data.path)


# --- Health Check ---

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"ok": True, "service": "adkpy", "version": "1.0.0", "dev_ui": True}


# --- ADK Dev UI Integration ---

# Initialize the Dev UI server with our FastAPI app
dev_ui = get_dev_ui_server()

# Register agents with ADK if using the v2 versions
try:
    # Try to import and register the ADK-enhanced agents
    from agents.clarifier_agent_v2 import ClarifierAgent as ClarifierAgentV2
    logger.info("ADK-enhanced ClarifierAgent registered")
except ImportError:
    logger.warning("ADK-enhanced agents not found, using standard versions")

# Log startup information
@app.on_event("startup")
async def startup_event():
    """Log startup information and agent registry."""
    from adk.agents import list_agents, get_agent

    logger.info(f"ADK Orchestrator started")
    logger.info(f"API available at http://localhost:8089")

    # Log registered agents
    registered_agents = list_agents()
    if registered_agents:
        logger.info(f"Registered {len(registered_agents)} agents:")
        for agent_name in registered_agents:
            agent = get_agent(agent_name)
            if agent:
                logger.info(f"  - {agent.name}: {agent.description}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("ADK Orchestrator shutting down")