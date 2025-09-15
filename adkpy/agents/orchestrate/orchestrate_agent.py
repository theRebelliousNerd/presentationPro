"""
Simplified orchestrate agent for PresentationPro using ADK's RemoteA2aAgent.
This coordinates all presentation agents via A2A protocol.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.genai import types

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class PresentationOrchestrator:
    """Orchestrates presentation creation workflow using remote A2A agents."""

    def __init__(self):
        self.agent_urls = {
            "clarifier": os.environ.get("CLARIFIER_URL", "http://clarifier:10001"),
            "outline": os.environ.get("OUTLINE_URL", "http://outline:10002"),
            "slide_writer": os.environ.get("SLIDE_WRITER_URL", "http://slide-writer:10003"),
            "critic": os.environ.get("CRITIC_URL", "http://critic:10004"),
            "notes_polisher": os.environ.get("NOTES_POLISHER_URL", "http://notes-polisher:10005"),
            "design": os.environ.get("DESIGN_URL", "http://design:10006"),
            "script_writer": os.environ.get("SCRIPT_WRITER_URL", "http://script-writer:10007"),
            "research": os.environ.get("RESEARCH_URL", "http://research:10008")
        }

        # Create RemoteA2aAgent instances for each service
        self.remote_agents = {}
        for name, url in self.agent_urls.items():
            try:
                self.remote_agents[name] = RemoteA2aAgent(
                    name=f"{name}_remote",
                    url=url,
                    description=f"Remote {name} agent for presentation creation"
                )
                log.info(f"Connected to {name} agent at {url}")
            except Exception as e:
                log.error(f"Failed to connect to {name} at {url}: {e}")

    def create_agent(self) -> Agent:
        """Create the main orchestrator agent with sub-agents."""

        # Get list of successfully connected agents
        sub_agents = list(self.remote_agents.values())

        # Create the orchestrator agent with remote agents as sub-agents
        orchestrator = Agent(
            name="presentation_orchestrator",
            model="gemini-2.0-flash",
            description="Orchestrates multi-agent presentation creation workflow",
            instruction="""You are the orchestrator for a presentation creation system.

            You coordinate the following specialized agents:
            1. Clarifier - Refines vague user requests into clear goals
            2. Outline - Creates presentation structure
            3. Slide Writer - Generates slide content
            4. Critic - Reviews and improves quality
            5. Notes Polisher - Enhances speaker notes
            6. Design - Creates visual specifications
            7. Script Writer - Generates full scripts
            8. Research - Gathers supporting data

            Workflow:
            1. First, use the clarifier to refine the user's goals
            2. Once goals are clear, use outline to create structure
            3. Use slide_writer to generate content for each slide
            4. Use critic to review and improve
            5. Optionally use enhancement agents (notes_polisher, design, script_writer)
            6. Use research agent when additional data is needed

            Always respond with structured JSON containing the workflow status and results.
            """,
            sub_agents=sub_agents if sub_agents else None
        )

        return orchestrator

    async def process_presentation_request(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a presentation creation request through the agent workflow."""

        results = {
            "status": "processing",
            "stages": {}
        }

        try:
            # Stage 1: Clarification
            if "clarifier" in self.remote_agents:
                clarify_input = {
                    "history": request.get("history", []),
                    "initialInput": request.get("initialInput", {}),
                    "newFiles": request.get("newFiles")
                }

                clarify_result = await self.remote_agents["clarifier"].execute(
                    types.Content(parts=[types.Part(text=json.dumps(clarify_input))])
                )
                results["stages"]["clarification"] = clarify_result

                # Check if clarification is complete
                if clarify_result.get("finished", False):
                    # Stage 2: Outline generation
                    if "outline" in self.remote_agents:
                        outline_input = {
                            "refinedGoals": clarify_result.get("response", ""),
                            "assets": request.get("assets")
                        }

                        outline_result = await self.remote_agents["outline"].execute(
                            types.Content(parts=[types.Part(text=json.dumps(outline_input))])
                        )
                        results["stages"]["outline"] = outline_result

                        # Continue with slide generation, critic, etc.
                        # This is simplified - actual implementation would continue the workflow

            results["status"] = "complete"

        except Exception as e:
            log.error(f"Workflow error: {e}")
            results["status"] = "error"
            results["error"] = str(e)

        return results


# Create global orchestrator instance
orchestrator = PresentationOrchestrator()

# Create the ADK agent
root_agent = orchestrator.create_agent()

log.info(f"Orchestrator agent '{root_agent.name}' created with {len(orchestrator.remote_agents)} remote agents")