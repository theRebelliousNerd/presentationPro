#!/usr/bin/env python3
"""
Launch ADK Dev UI with PresentationPro Agents
"""

import os
import sys
import argparse
import logging

# Set up environment
os.environ.setdefault("GOOGLE_GENAI_API_KEY", "your-key-here")

# Add paths
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_agents():
    """Create and configure all presentation agents."""
    # Get API key
    api_key = os.getenv("GOOGLE_GENAI_API_KEY")
    if not api_key or api_key == "your-key-here":
        logger.error("Please set GOOGLE_GENAI_API_KEY environment variable")
        sys.exit(1)

    # Create a simple LLM wrapper for agents
    class SimpleLLM:
        def __init__(self, api_key):
            self.api_key = api_key

    # Import agent classes
    from agents.clarifier.agent import ClarifierADKAgent
    from agents.outline.agent import OutlineADKAgent
    from agents.slide_writer.agent import SlideWriterADKAgent
    from agents.critic.agent import CriticADKAgent
    from agents.notes_polisher.agent import NotesPolisherADKAgent
    from agents.design.agent import DesignADKAgent
    from agents.script_writer.agent import ScriptWriterADKAgent
    from agents.research.agent import ResearchADKAgent

    # Create agent instances
    agents = [
        ClarifierADKAgent(llm=llm, name="Clarifier", description="Refines presentation goals"),
        OutlineADKAgent(llm=llm, name="Outline", description="Creates presentation structure"),
        SlideWriterADKAgent(llm=llm, name="SlideWriter", description="Generates slide content"),
        CriticADKAgent(llm=llm, name="Critic", description="Reviews and improves slides"),
        NotesPolisherADKAgent(llm=llm, name="NotesPolisher", description="Enhances speaker notes"),
        DesignADKAgent(llm=llm, name="Design", description="Creates visual designs"),
        ScriptWriterADKAgent(llm=llm, name="ScriptWriter", description="Assembles presenter script"),
        ResearchADKAgent(llm=llm, name="Research", description="Gathers background information"),
    ]

    logger.info(f"Created {len(agents)} agents")
    return agents


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Launch ADK Dev UI")
    parser.add_argument("--port", type=int, default=8100, help="Port number")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address")
    args = parser.parse_args()

    try:
        # Create agents
        agents = create_agents()

        # Import and run ADK dev
        from google.adk import dev

        logger.info(f"Starting ADK Dev UI on http://{args.host}:{args.port}")
        logger.info("Press Ctrl+C to stop")

        # Run the dev server
        dev.run(
            agents=agents,
            port=args.port,
            host=args.host,
            title="PresentationPro Agent Development",
            description="Test and evaluate presentation generation agents"
        )

    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure Google ADK is installed: pip install google-adk")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()