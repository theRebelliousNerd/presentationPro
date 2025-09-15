#!/usr/bin/env python3
"""
Simplified ADK Dev UI Launcher for PresentationPro
"""

import os
import sys
import argparse

# Add agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

def main():
    """Launch ADK Dev UI with our agents."""
    parser = argparse.ArgumentParser(description="Launch ADK Dev UI")
    parser.add_argument("--port", type=int, default=8100, help="Port number")
    args = parser.parse_args()

    # Import agents
    from agents.clarifier.agent import clarifier_agent
    from agents.outline.agent import outline_agent
    from agents.slide_writer.agent import slide_writer_agent
    from agents.critic.agent import critic_agent
    from agents.notes_polisher.agent import notes_polisher_agent
    from agents.design.agent import design_agent
    from agents.script_writer.agent import script_writer_agent
    from agents.research.agent import research_agent

    # Create agent list
    agents = [
        clarifier_agent,
        outline_agent,
        slide_writer_agent,
        critic_agent,
        notes_polisher_agent,
        design_agent,
        script_writer_agent,
        research_agent
    ]

    print(f"Starting ADK Dev UI on port {args.port}")
    print(f"Agents loaded: {[agent.name for agent in agents]}")

    # Import and run ADK dev server
    from google.adk import dev

    # Run the dev server
    dev.run(
        agents=agents,
        port=args.port,
        host="0.0.0.0"
    )

if __name__ == "__main__":
    main()