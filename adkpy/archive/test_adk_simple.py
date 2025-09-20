import pytest

pytest.skip("Legacy ADK dev helpers not available", allow_module_level=True)
pytestmark = pytest.mark.skip(reason="Legacy ADK dev helpers not available")

#!/usr/bin/env python3
"""
Simple ADK Dev UI Test
"""

import os
os.environ.setdefault("GOOGLE_GENAI_API_KEY", "test-key")

from google.adk import dev
from google.adk.agents import Agent

# Create minimal test agents
class TestAgent(Agent):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.description = f"Test agent: {name}"

    def run(self, input_data):
        return {"message": f"Hello from {self.name}", "input": input_data}

# Create agent instances
agents = [
    TestAgent("Clarifier"),
    TestAgent("Outline"),
    TestAgent("SlideWriter"),
    TestAgent("Critic"),
]

print("Starting ADK Dev UI on http://localhost:8100")
print("Agents:", [a.name for a in agents])

# Run dev UI
dev.run(
    agents=agents,
    port=8100,
    host="127.0.0.1"
)
