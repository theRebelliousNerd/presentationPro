#!/usr/bin/env python3
"""
Launch ADK Dev UI for PresentationPro agents.

This script launches the Google ADK Dev UI to test and debug
the presentation generation agents.
"""

import os
import sys
from pathlib import Path

# Add the adkpy directory to Python path
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir))

# Import ADK dev module
try:
    from google.adk import dev
except ImportError:
    print("Error: Google ADK not installed")
    print("Please install it with: pip install google-adk")
    sys.exit(1)

def main():
    """Launch the ADK Dev UI with explicitly loaded agents."""

    # Check for API key
    api_key = os.environ.get("GOOGLE_GENAI_API_KEY")
    if not api_key:
        print("Error: GOOGLE_GENAI_API_KEY environment variable not set")
        print("Please set it with: export GOOGLE_GENAI_API_KEY=your_key_here")
        sys.exit(1)

    # Import all agents explicitly
    agents_list = []
    agent_names = []

    try:
        # Import each agent's root_agent
        from agents.clarifier.agent import root_agent as clarifier
        agents_list.append(clarifier)
        agent_names.append("clarifier")
    except ImportError as e:
        print(f"Warning: Could not import clarifier agent: {e}")

    try:
        from agents.outline.agent import root_agent as outline
        agents_list.append(outline)
        agent_names.append("outline")
    except ImportError as e:
        print(f"Warning: Could not import outline agent: {e}")

    try:
        from agents.slide_writer.agent import root_agent as slide_writer
        agents_list.append(slide_writer)
        agent_names.append("slide_writer")
    except ImportError as e:
        print(f"Warning: Could not import slide_writer agent: {e}")

    try:
        from agents.critic.agent import root_agent as critic
        agents_list.append(critic)
        agent_names.append("critic")
    except ImportError as e:
        print(f"Warning: Could not import critic agent: {e}")

    try:
        from agents.notes_polisher.agent import root_agent as notes_polisher
        agents_list.append(notes_polisher)
        agent_names.append("notes_polisher")
    except ImportError as e:
        print(f"Warning: Could not import notes_polisher agent: {e}")

    try:
        from agents.design.agent import root_agent as design
        agents_list.append(design)
        agent_names.append("design")
    except ImportError as e:
        print(f"Warning: Could not import design agent: {e}")

    try:
        from agents.script_writer.agent import root_agent as script_writer
        agents_list.append(script_writer)
        agent_names.append("script_writer")
    except ImportError as e:
        print(f"Warning: Could not import script_writer agent: {e}")

    try:
        from agents.research.agent import root_agent as research
        agents_list.append(research)
        agent_names.append("research")
    except ImportError as e:
        print(f"Warning: Could not import research agent: {e}")

    # Launch ADK Dev UI
    print("=" * 60)
    print("Launching ADK Dev UI for PresentationPro Agents")
    print("=" * 60)
    print(f"Working directory: {script_dir}")
    print(f"API Key: {'*' * 20}{api_key[-4:]}")
    print()
    print(f"Successfully loaded {len(agents_list)} agents:")
    for name in agent_names:
        print(f"  ✓ {name}")
    print()
    print("Agent Microservice Ports (when running standalone):")
    print("  - clarifier: 10001")
    print("  - outline: 10002")
    print("  - slide_writer: 10003")
    print("  - critic: 10004")
    print("  - notes_polisher: 10005")
    print("  - design: 10006")
    print("  - script_writer: 10007")
    print("  - research: 10008")
    print()
    print("Starting ADK Dev UI on http://localhost:8100")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    try:
        # Run Dev UI with explicitly loaded agents
        dev.run(
            agents=agents_list,
            port=8100,
            host="0.0.0.0",  # Bind to all interfaces for Docker
            title="PresentationPro Agents",
            description="Test presentation generation agents"
        )
    except KeyboardInterrupt:
        print("\n\nADK Dev UI stopped by user")
    except Exception as e:
        print(f"\nError running ADK Dev UI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()