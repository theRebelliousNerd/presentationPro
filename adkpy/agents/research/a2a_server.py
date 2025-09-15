from a2a.server.apps import A2AStarletteApplication
from a2a.types import AgentCard, AgentCapabilities, AgentSkill
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
import os
import logging
from dotenv import load_dotenv
from research.agent_executor import ResearchAgentExecutor
import uvicorn
from research import agent

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host = os.environ.get("A2A_HOST", "localhost")
port = int(os.environ.get("A2A_PORT", 8080))
PUBLIC_URL = os.environ.get("PUBLIC_URL")

class ResearchAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self._agent = self._build_agent()
        self.runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="research_design_practices",
            name="Research Design Best Practices",
            description="Researches and curates evidence-based best practices for presentation design.",
            tags=["research", "design", "presentation"],
            examples=[
                "Research best practices for accessible presentation backgrounds.",
            ],
        )
        self.agent_card = AgentCard(
            name="Research Agent",
            description="Researches design best practices and gathers information.",
            url=f"{PUBLIC_URL}",
            version="1.0.0",
            defaultInputModes=ResearchAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=ResearchAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

    def _build_agent(self) -> LlmAgent:
        return agent.root_agent

if __name__ == '__main__':
    try:
        researchAgent = ResearchAgent()
        request_handler = DefaultRequestHandler(
            agent_executor=ResearchAgentExecutor(researchAgent.runner, researchAgent.agent_card),
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(
            agent_card=researchAgent.agent_card,
            http_handler=request_handler,
        )
        logger.info(f"Attempting to start server with Agent Card: {researchAgent.agent_card.name}")
        uvicorn.run(server.build(), host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)