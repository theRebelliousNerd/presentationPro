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
from notes_polisher.agent_executor import NotesPolisherAgentExecutor
import uvicorn
from notes_polisher import agent

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host = os.environ.get("A2A_HOST", "localhost")
port = int(os.environ.get("A2A_PORT", 8080))
PUBLIC_URL = os.environ.get("PUBLIC_URL")

class NotesPolisherAgent:
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
            id="polish_speaker_notes",
            name="Polish Speaker Notes",
            description="Refines and rephrases speaker notes to match a desired tone and style.",
            tags=["notes", "polish", "writing"],
            examples=[
                "Polish these notes to sound more professional.",
            ],
        )
        self.agent_card = AgentCard(
            name="Notes Polisher Agent",
            description="Refines speaker notes for optimal tone and presenter readability.",
            url=f"{PUBLIC_URL}",
            version="1.0.0",
            defaultInputModes=NotesPolisherAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=NotesPolisherAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

    def _build_agent(self) -> LlmAgent:
        return agent.root_agent

if __name__ == '__main__':
    try:
        notesPolisherAgent = NotesPolisherAgent()
        request_handler = DefaultRequestHandler(
            agent_executor=NotesPolisherAgentExecutor(notesPolisherAgent.runner, notesPolisherAgent.agent_card),
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(
            agent_card=notesPolisherAgent.agent_card,
            http_handler=request_handler,
        )
        logger.info(f"Attempting to start server with Agent Card: {notesPolisherAgent.agent_card.name}")
        uvicorn.run(server.build(), host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)