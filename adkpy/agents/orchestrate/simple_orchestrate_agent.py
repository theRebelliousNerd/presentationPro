"""
Simple orchestrate agent for PresentationPro using ADK.
This version uses sub-agents pattern for local development.
"""

import os
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

from google.adk import Agent
from google.genai import types

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def create_orchestrator_agent() -> Agent:
    """Create the orchestrator agent using ADK's sub-agents pattern."""

    # For now, we'll create a simple orchestrator without remote connections
    # In production, this would connect to the other agents via A2A
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
        1. First, refine the user's goals through clarification
        2. Once goals are clear, create a presentation outline
        3. Generate content for each slide
        4. Review and improve with the critic
        5. Optionally enhance with notes, design, and script
        6. Use research when additional data is needed

        For now, simulate the workflow and respond with structured JSON containing the workflow status.

        Input Format: JSON with request details
        Output Format: JSON with workflow results
        """
    )

    return orchestrator

# Create the root agent
root_agent = create_orchestrator_agent()

log.info(f"Simple orchestrator agent '{root_agent.name}' created.")