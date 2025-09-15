#!/usr/bin/env python
"""
Test script to verify ADK backend functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all critical imports"""
    print("Testing ADK module imports...")

    try:
        # Test ADK core imports
        import adk
        from adk.agents import Agent, LlmAgent, BaseAgent
        from adk.tools import Tool, ToolResult
        from adk.dev_ui import get_dev_ui_server
        print("[OK] ADK core modules imported successfully")

        # Test google.adk namespace
        from google.adk.agents import Agent as GoogleAgent
        print("[OK] google.adk namespace working")

        # Test agent wrappers
        from agents.wrappers import (
            ClarifierAgent, OutlineAgent, SlideWriterAgent,
            CriticAgent, DesignAgent, NotesPolisherAgent,
            ScriptWriterAgent, ResearchAgent
        )
        print("[OK] Agent wrappers imported successfully")

        # Test tools (but catch ArangoDB connection errors)
        try:
            from tools import (
                ArangoGraphRAGTool, VisionContrastTool,
                WebSearchTool, TelemetryTool
            )
            print("[OK] Tools imported (ArangoDB connection warnings expected)")
        except Exception as e:
            print(f"[WARNING] Tools import warning: {e}")

        # Test main app creation
        from app.main import app
        print("[OK] FastAPI app created successfully")

        print("\n[SUCCESS] All critical imports successful!")
        print("The ADK backend is properly configured and ready to run.")

        return True

    except ImportError as e:
        print(f"\n[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return False

def test_agent_creation():
    """Test creating ADK agents"""
    print("\nTesting agent creation...")

    try:
        from adk.agents import Agent, register_agent, list_agents

        # Create a test agent
        test_agent = Agent(
            name="test_agent",
            model="gemini-2.0-flash",
            description="A test agent",
            instruction="You are a test agent"
        )

        # Register it
        register_agent(test_agent)

        # Check if it's registered
        agents = list_agents()
        if "test_agent" in agents:
            print("[OK] Agent creation and registration working")
            return True
        else:
            print("[ERROR] Agent registration failed")
            return False

    except Exception as e:
        print(f"[ERROR] Agent creation error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("ADK Backend Integration Test")
    print("=" * 60)

    # Set a dummy API key to avoid warnings
    os.environ['GOOGLE_GENAI_API_KEY'] = 'test-key-for-import-testing'

    results = []

    # Run tests
    results.append(test_imports())
    results.append(test_agent_creation())

    # Summary
    print("\n" + "=" * 60)
    if all(results):
        print("[SUCCESS] ALL TESTS PASSED - Backend is ready!")
        print("\nYou can now start the backend with:")
        print("  docker compose up --build adkpy")
        print("\nOr run locally with:")
        print("  cd adkpy && uvicorn app.main:app --reload --port 8089")
    else:
        print("[ERROR] Some tests failed - please review the errors above")
    print("=" * 60)

if __name__ == "__main__":
    main()