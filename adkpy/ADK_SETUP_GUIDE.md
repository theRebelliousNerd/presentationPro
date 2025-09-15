# ADK Setup Guide for PresentationPro

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Agent Directory Structure](#agent-directory-structure)
4. [Environment Setup](#environment-setup)
5. [Installing ADK](#installing-adk)
6. [Configuration](#configuration)
7. [Running ADK Dev UI](#running-adk-dev-ui)
8. [Troubleshooting Setup Issues](#troubleshooting-setup-issues)

## Prerequisites

### Required Software
- Python 3.10 or higher
- pip (Python package manager)
- Google Cloud SDK (for deployment)
- Docker (optional, for containerization)

### Google Cloud Requirements
- Google Cloud Project with billing enabled
- APIs to enable:
  - Vertex AI API
  - Cloud Run API
  - Cloud Build API
  - Artifact Registry API
  - Spanner API (if using graph database)

### API Keys
- `GOOGLE_GENAI_API_KEY` - Required for Gemini API access
- `BING_SEARCH_API_KEY` - Optional for web search functionality

## Project Structure

The ADK framework expects a specific project structure. Your presentation system should be organized as follows:

```
presentationPro/
├── adkpy/                          # Main ADK directory
│   ├── agents/                     # Agent implementations
│   │   ├── clarifier/              # Clarifier agent
│   │   │   ├── agent.py            # REQUIRED: Agent definition
│   │   │   ├── __init__.py         # Makes it a Python package
│   │   │   ├── requirements.txt    # Agent-specific dependencies
│   │   │   ├── a2a_server.py       # A2A server wrapper (optional)
│   │   │   └── .env                # Agent-specific environment vars
│   │   ├── outline/                # Outline agent
│   │   │   ├── agent.py            # REQUIRED: Agent definition
│   │   │   └── ...
│   │   ├── slide_writer/           # Slide writer agent
│   │   │   ├── agent.py            # REQUIRED: Agent definition
│   │   │   └── ...
│   │   ├── critic/                 # Critic agent
│   │   │   ├── agent.py            # REQUIRED: Agent definition
│   │   │   └── ...
│   │   ├── notes_polisher/         # Notes polisher agent
│   │   │   ├── agent.py            # REQUIRED: Agent definition
│   │   │   └── ...
│   │   ├── design/                 # Design agent
│   │   │   ├── agent.py            # REQUIRED: Agent definition
│   │   │   └── ...
│   │   ├── script_writer/          # Script writer agent
│   │   │   ├── agent.py            # REQUIRED: Agent definition
│   │   │   └── ...
│   │   └── research/               # Research agent
│   │       ├── agent.py            # REQUIRED: Agent definition
│   │       └── ...
│   ├── tools/                      # Shared tools
│   │   └── presentation_tools/
│   │       ├── __init__.py
│   │       └── mcp_server.py      # MCP server implementation
│   ├── app/                        # Application code
│   │   ├── main.py                 # FastAPI backend
│   │   ├── llm.py                  # LLM wrapper
│   │   └── ...
│   ├── requirements.txt            # Global dependencies
│   └── .env                        # Global environment variables
```

## Agent Directory Structure

**CRITICAL**: Each agent MUST have its own subdirectory under `agents/` with an `agent.py` file.

### Required: agent.py Structure

Each `agent.py` file MUST define a `root_agent` variable:

```python
from google.adk.agents import Agent

# REQUIRED: root_agent variable
root_agent = Agent(
    name="clarifier_agent",           # Unique agent name
    model="gemini-2.0-flash",         # Model to use
    description="Refines presentation goals through Q&A",
    instruction="""
    You are a Clarifier agent. Your role is to ask targeted questions
    to help refine a user's presentation request.
    """,
    tools=[]  # Optional: List of tools
)

# Optional: Additional agents for multi-agent systems
agents = []  # List of sub-agents if needed
```

### Alternative: Agent Class Pattern

You can also define agents using classes:

```python
from google.adk.agents import LlmAgent, BaseAgent
from google.adk.tools import google_search

class ClarifierAgent:
    def __init__(self):
        self.agent = self._build_agent()

    def _build_agent(self) -> LlmAgent:
        return LlmAgent(
            name="clarifier_agent",
            model="gemini-2.0-flash",
            description="Refines presentation goals",
            instruction=self.get_instruction(),
            tools=[google_search]
        )

    def get_instruction(self):
        return """Your instructions here..."""

# REQUIRED: Instantiate and expose root_agent
clarifier = ClarifierAgent()
root_agent = clarifier.agent
```

## Environment Setup

### 1. Create Virtual Environment

```bash
cd presentationPro/adkpy
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### 2. Set Environment Variables

Create `.env` file in `adkpy/` directory:

```bash
# Required
GOOGLE_GENAI_API_KEY=your_api_key_here
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Optional for Vertex AI
GOOGLE_GENAI_USE_VERTEXAI=FALSE  # Set TRUE to use Vertex AI

# Optional for tools
BING_SEARCH_API_KEY=your_bing_key_here
WEB_SEARCH_CACHE=.cache/web-search.json

# For Spanner (if using graph database)
SPANNER_INSTANCE_ID=your-instance
SPANNER_DATABASE_ID=your-database

# For MCP Server
MCP_SERVER_URL=http://localhost:8080/sse
```

### 3. Agent-Specific Environment

Each agent can have its own `.env` file:

```bash
# agents/clarifier/.env
MODEL_NAME=gemini-2.0-flash
MAX_TOKENS=2000
TEMPERATURE=0.7
```

## Installing ADK

### 1. Install Core ADK Package

```bash
pip install google-adk
```

### 2. Install Additional Dependencies

```bash
# Global dependencies
pip install -r requirements.txt

# Agent-specific dependencies (for each agent)
cd agents/clarifier
pip install -r requirements.txt
cd ../..
```

### 3. Verify Installation

```bash
python -c "from google.adk import dev; print('ADK installed successfully')"
```

## Configuration

### 1. Configure ADK Settings

Create `adk.yaml` in the project root:

```yaml
name: presentation-pro
version: 1.0.0
agents:
  directory: agents
  auto_discover: true
tools:
  directory: tools
dev:
  port: 8100
  host: 127.0.0.1
  auto_reload: true
```

### 2. Configure Logging

```python
# In your agent.py files
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

## Running ADK Dev UI

### 1. Basic Launch

From the `adkpy` directory:

```bash
# Activate virtual environment
source env/bin/activate  # On Windows: env\Scripts\activate

# Set environment variables
source .env  # On Windows: use set commands or dotenv

# Launch ADK Dev UI
adk web --port 8100
```

### 2. Launch with Specific Agent Directory

If ADK isn't discovering agents:

```bash
cd adkpy/agents
adk web --port 8100
```

### 3. Launch Script

Create `launch_adk.sh`:

```bash
#!/bin/bash
cd /path/to/presentationPro/adkpy
source env/bin/activate
export GOOGLE_GENAI_API_KEY=your_key_here
cd agents
adk web --port 8100 --host 0.0.0.0
```

### 4. Python Launch Script

Create `launch_dev_ui.py`:

```python
#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Set up paths
project_root = Path(__file__).parent
agents_dir = project_root / "agents"

# Set environment
os.environ.setdefault("GOOGLE_GENAI_API_KEY", "your-key")
os.chdir(agents_dir)

# Import and run ADK dev
from google.adk import dev

# Import all agents to ensure they're registered
from clarifier.agent import root_agent as clarifier
from outline.agent import root_agent as outline
from slide_writer.agent import root_agent as slide_writer
from critic.agent import root_agent as critic
from notes_polisher.agent import root_agent as notes_polisher
from design.agent import root_agent as design
from script_writer.agent import root_agent as script_writer
from research.agent import root_agent as research

# Create agents list
agents = [
    clarifier,
    outline,
    slide_writer,
    critic,
    notes_polisher,
    design,
    script_writer,
    research
]

# Run dev UI
dev.run(
    agents=agents,
    port=8100,
    host="127.0.0.1",
    title="PresentationPro Agent Development",
    description="Multi-agent presentation generation system"
)
```

## Troubleshooting Setup Issues

### Issue: ADK Dev UI Shows Directory Names Instead of Agents

**Cause**: ADK is not finding the `agent.py` files or `root_agent` definitions.

**Solutions**:

1. **Verify File Structure**:
   ```bash
   # Check each agent has agent.py
   ls -la agents/*/agent.py
   ```

2. **Verify root_agent Definition**:
   ```python
   # Each agent.py MUST have:
   root_agent = Agent(...)  # or LlmAgent(...)
   ```

3. **Launch from Correct Directory**:
   ```bash
   cd adkpy/agents
   adk web --port 8100
   ```

4. **Use Explicit Agent Loading**:
   ```python
   from google.adk import dev
   from clarifier.agent import root_agent

   dev.run(agents=[root_agent], port=8100)
   ```

### Issue: Module Import Errors

**Solutions**:

1. **Add __init__.py files**:
   ```bash
   touch agents/__init__.py
   touch agents/clarifier/__init__.py
   ```

2. **Update PYTHONPATH**:
   ```bash
   export PYTHONPATH=$PYTHONPATH:/path/to/adkpy
   ```

### Issue: API Key Not Found

**Solutions**:

1. **Set in environment**:
   ```bash
   export GOOGLE_GENAI_API_KEY=your_key
   ```

2. **Use python-dotenv**:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

### Issue: Port Already in Use

**Solutions**:

1. **Use different port**:
   ```bash
   adk web --port 8101
   ```

2. **Kill existing process**:
   ```bash
   lsof -i :8100
   kill -9 <PID>
   ```

## Next Steps

After successful setup:

1. Test each agent in ADK Dev UI
2. Implement agent-to-agent communication (A2A)
3. Add MCP server integration for tools
4. Deploy agents to Cloud Run or Agent Engine
5. Integrate with your presentation frontend

See other documentation files for detailed guides on these topics.