# ADK Dev UI Guide for PresentationPro

## Table of Contents
1. [Overview](#overview)
2. [Dev UI Architecture](#dev-ui-architecture)
3. [Launching the Dev UI](#launching-the-dev-ui)
4. [UI Components](#ui-components)
5. [Agent Discovery](#agent-discovery)
6. [Testing Agents](#testing-agents)
7. [Evaluation Framework](#evaluation-framework)
8. [Debugging Tools](#debugging-tools)
9. [Common Issues and Solutions](#common-issues-and-solutions)
10. [Advanced Features](#advanced-features)

## Overview

The ADK Dev UI is an interactive web interface for developing, testing, and debugging AI agents. It provides:

- **Agent Discovery**: Automatically finds and loads agents
- **Interactive Chat**: Test agents with real-time responses
- **Event Viewer**: See detailed execution traces
- **Tool Monitoring**: Track tool calls and responses
- **Performance Metrics**: Monitor latency and token usage
- **Evaluation Tools**: Run test suites against agents

## Dev UI Architecture

### How ADK Dev UI Works

```
User Request → Dev UI → Agent Discovery → Agent Loading → Execution → Response
                ↓           ↓                ↓              ↓
            Web Interface  File System    Import & Init   Runner
                           Scanning       Registration    Service
```

### Agent Discovery Process

1. **Directory Scan**: ADK scans for `agent.py` files
2. **Import Modules**: Dynamically imports Python modules
3. **Find root_agent**: Looks for `root_agent` variable
4. **Register Agents**: Adds agents to available list
5. **Initialize UI**: Populates dropdown with agent names

## Launching the Dev UI

### Method 1: Basic Launch

```bash
# From adkpy directory
cd presentationPro/adkpy
source env/bin/activate
adk web --port 8100
```

### Method 2: From Agents Directory

```bash
# This ensures ADK finds all agents
cd presentationPro/adkpy/agents
adk web --port 8100
```

### Method 3: Programmatic Launch

```python
#!/usr/bin/env python3
# launch_dev_ui.py

from google.adk import dev
import os

# Import all your agents
from agents.clarifier.agent import root_agent as clarifier
from agents.outline.agent import root_agent as outline
from agents.slide_writer.agent import root_agent as slide_writer
from agents.critic.agent import root_agent as critic
from agents.notes_polisher.agent import root_agent as notes_polisher
from agents.design.agent import root_agent as design
from agents.script_writer.agent import root_agent as script_writer
from agents.research.agent import root_agent as research

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

# Run Dev UI
dev.run(
    agents=agents,
    port=8100,
    host="127.0.0.1",
    title="PresentationPro Agents",
    description="Test presentation generation agents"
)
```

### Method 4: Docker Launch

```dockerfile
# Dockerfile for ADK Dev UI
FROM python:3.10-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy agents
COPY agents/ agents/
COPY tools/ tools/

# Environment variables
ENV GOOGLE_GENAI_API_KEY=${GOOGLE_GENAI_API_KEY}
ENV PYTHONPATH=/app

# Launch script
COPY launch_dev_ui.py .

# Expose port
EXPOSE 8100

# Run Dev UI
CMD ["python", "launch_dev_ui.py"]
```

```bash
# Build and run
docker build -t adk-dev-ui .
docker run -p 8100:8100 -e GOOGLE_GENAI_API_KEY=your_key adk-dev-ui
```

## UI Components

### 1. Agent Selector

Located in the top-right corner, this dropdown shows all discovered agents:

```
┌─────────────────────────┐
│ ▼ Select Agent          │
├─────────────────────────┤
│ • clarifier             │
│ • outline               │
│ • slide_writer          │
│ • critic                │
│ • notes_polisher        │
│ • design                │
│ • script_writer         │
│ • research              │
└─────────────────────────┘
```

**Troubleshooting**: If you see directory names instead of agent names, see [Agent Discovery](#agent-discovery) section.

### 2. Chat Interface

Main interaction area for testing agents:

```
┌──────────────────────────────────────────┐
│ Chat                                     │
├──────────────────────────────────────────┤
│ User: Create a presentation about AI    │
│                                          │
│ Agent: I'll help you create a            │
│ presentation about AI. Let me ask a      │
│ few questions first...                   │
│                                          │
│ [Input field...........................]  │
│ [Send]                                   │
└──────────────────────────────────────────┘
```

### 3. Events Tab

Shows detailed execution trace:

```
┌──────────────────────────────────────────┐
│ Events                                   │
├──────────────────────────────────────────┤
│ ► agent_start                            │
│   └─ clarifier_agent                     │
│ ► tool_call                              │
│   └─ google_search("AI trends 2024")    │
│ ► tool_response                          │
│   └─ [search results...]                │
│ ► agent_complete                         │
│   └─ duration: 2.3s, tokens: 1,234      │
└──────────────────────────────────────────┘
```

### 4. State Inspector

View and modify agent state:

```
┌──────────────────────────────────────────┐
│ State                                    │
├──────────────────────────────────────────┤
│ {                                        │
│   "conversation_id": "abc123",           │
│   "slides_created": 5,                   │
│   "current_section": "conclusion",       │
│   "quality_score": 8.5,                  │
│   "tokens_used": 5432                    │
│ }                                        │
└──────────────────────────────────────────┘
```

### 5. Tools Monitor

Track tool usage:

```
┌──────────────────────────────────────────┐
│ Tools                                    │
├──────────────────────────────────────────┤
│ Tool: google_search                      │
│ Calls: 3                                 │
│ Avg Duration: 450ms                      │
│                                          │
│ Tool: generate_image                     │
│ Calls: 8                                 │
│ Avg Duration: 2.1s                       │
└──────────────────────────────────────────┘
```

## Agent Discovery

### How ADK Discovers Agents

ADK uses a specific discovery pattern:

1. **Scans directories** for `agent.py` files
2. **Imports modules** dynamically
3. **Looks for `root_agent`** variable
4. **Validates agent** has required attributes
5. **Registers agent** in UI

### Required Agent Structure

Each agent directory must have:

```
agents/
├── clarifier/
│   ├── __init__.py          # Makes it a Python package
│   ├── agent.py             # MUST define root_agent
│   └── requirements.txt     # Optional dependencies
```

### Agent.py Requirements

```python
# MINIMUM REQUIRED STRUCTURE
from google.adk.agents import Agent

root_agent = Agent(
    name="clarifier",        # REQUIRED: Unique name
    model="gemini-2.0-flash", # REQUIRED: Model
    description="...",       # REQUIRED: Description
    instruction="..."        # REQUIRED: Instructions
)
```

### Fixing Discovery Issues

If ADK shows directory names instead of agents:

1. **Check File Names**:
   ```bash
   # Verify agent.py exists
   ls -la agents/*/agent.py
   ```

2. **Check root_agent Definition**:
   ```python
   # In each agent.py
   print(root_agent)  # Should print agent object
   ```

3. **Check Python Path**:
   ```python
   import sys
   print(sys.path)  # Should include agents directory
   ```

4. **Check Imports**:
   ```python
   # Test import manually
   from clarifier.agent import root_agent
   print(root_agent.name)  # Should print agent name
   ```

5. **Use Explicit Loading**:
   ```python
   from google.adk import dev

   # Explicitly import agents
   from clarifier.agent import root_agent as clarifier
   from outline.agent import root_agent as outline

   # Pass to dev.run
   dev.run(agents=[clarifier, outline], port=8100)
   ```

## Testing Agents

### Basic Testing

1. **Select Agent**: Choose from dropdown
2. **Enter Query**: Type test input
3. **Send Message**: Click send or press Enter
4. **Review Response**: Check output quality
5. **Check Events**: View execution details

### Test Scenarios

```python
# Create test_scenarios.py
test_cases = [
    {
        "agent": "clarifier",
        "input": "I need a presentation about AI",
        "expected": ["audience", "duration", "objective"]
    },
    {
        "agent": "outline",
        "input": "Create outline for 20-min AI presentation",
        "expected": ["introduction", "main points", "conclusion"]
    },
    {
        "agent": "slide_writer",
        "input": "Write slide about machine learning benefits",
        "expected": ["headline", "bullets", "speaker_notes"]
    }
]

# Run tests in Dev UI
for test in test_cases:
    print(f"Testing {test['agent']}: {test['input']}")
    # Manually verify response contains expected elements
```

### Multi-Agent Testing

Test agent interactions:

```python
# Test sequential flow
workflow = [
    ("clarifier", "Create AI presentation"),
    ("outline", "{use_previous_output}"),
    ("slide_writer", "{use_previous_output}")
]

# Execute in Dev UI and verify handoffs
```

## Evaluation Framework

### Creating Evaluations

```python
# evaluations/presentation_eval.py
from google.adk.evaluation import Evaluation, Match

class PresentationEvaluation:
    def __init__(self):
        self.evaluations = []

    def add_clarifier_eval(self):
        """Evaluate clarifier agent."""

        eval = Evaluation(
            name="clarifier_evaluation",
            agent_name="clarifier",
            test_cases=[
                {
                    "input": "I need a sales presentation",
                    "expected_contains": [
                        "audience",
                        "duration",
                        "objective"
                    ],
                    "expected_questions": 3
                },
                {
                    "input": "Technical presentation for developers",
                    "expected_contains": [
                        "technical depth",
                        "code examples",
                        "architecture"
                    ]
                }
            ]
        )

        self.evaluations.append(eval)

    def add_outline_eval(self):
        """Evaluate outline agent."""

        eval = Evaluation(
            name="outline_evaluation",
            agent_name="outline",
            test_cases=[
                {
                    "input": {
                        "topic": "AI in Healthcare",
                        "duration": 20,
                        "audience": "medical professionals"
                    },
                    "expected_structure": {
                        "has_introduction": True,
                        "main_sections": 3,
                        "has_conclusion": True,
                        "total_slides": 10-15
                    }
                }
            ]
        )

        self.evaluations.append(eval)

    def run_all(self):
        """Run all evaluations."""

        results = {}
        for eval in self.evaluations:
            result = eval.run()
            results[eval.name] = result

        return results
```

### Running Evaluations in Dev UI

1. **Navigate to Evaluations Tab**
2. **Select Test Suite**
3. **Click Run Evaluations**
4. **Review Results**:
   - Pass/Fail status
   - Match scores
   - Performance metrics
   - Error details

### Match Scoring

```python
# Example match scoring
def score_presentation_quality(output: str) -> float:
    """Score presentation output quality."""

    score = 0.0

    # Check structure
    if "introduction" in output.lower():
        score += 0.2
    if "conclusion" in output.lower():
        score += 0.2

    # Check content depth
    bullet_count = output.count("•")
    if bullet_count >= 10:
        score += 0.3

    # Check formatting
    if "**" in output or "##" in output:  # Markdown formatting
        score += 0.2

    # Check completeness
    if len(output) > 1000:
        score += 0.1

    return min(score, 1.0)  # Cap at 1.0
```

## Debugging Tools

### 1. Event Trace Analysis

View detailed execution flow:

```javascript
// Event structure in Dev UI
{
  "event_id": "evt_123",
  "timestamp": "2024-01-15T10:30:00Z",
  "type": "tool_call",
  "agent": "research_agent",
  "tool": "google_search",
  "arguments": {
    "query": "AI trends 2024"
  },
  "duration_ms": 450,
  "status": "success"
}
```

### 2. Token Usage Monitoring

Track token consumption:

```python
# In Events tab, look for:
{
  "token_usage": {
    "prompt_tokens": 1234,
    "completion_tokens": 567,
    "total_tokens": 1801,
    "cost_estimate": "$0.05"
  }
}
```

### 3. Error Debugging

Common error patterns:

```python
# Import errors
ERROR: No module named 'clarifier'
SOLUTION: Check PYTHONPATH and __init__.py files

# Agent not found
ERROR: root_agent not defined
SOLUTION: Ensure agent.py has root_agent = Agent(...)

# Tool errors
ERROR: Tool 'google_search' not found
SOLUTION: Import and register tool properly

# Model errors
ERROR: Invalid model name
SOLUTION: Use correct model name (e.g., "gemini-2.0-flash")
```

### 4. Performance Profiling

```python
# Add timing to agents
import time

class TimedAgent:
    def __init__(self, agent):
        self.agent = agent
        self.timings = []

    def run(self, input_text):
        start = time.time()
        result = self.agent.run(input_text)
        duration = time.time() - start

        self.timings.append({
            "input_length": len(input_text),
            "output_length": len(result),
            "duration": duration,
            "tokens_per_second": len(result) / duration
        })

        return result
```

## Common Issues and Solutions

### Issue 1: Agents Not Appearing in Dropdown

**Problem**: Dev UI shows directory names or no agents

**Solution**:
```python
# Fix 1: Ensure proper structure
agents/
├── clarifier/
│   ├── __init__.py       # REQUIRED
│   └── agent.py          # REQUIRED with root_agent

# Fix 2: Check imports
from google.adk.agents import Agent
root_agent = Agent(...)   # MUST be named root_agent

# Fix 3: Launch from correct directory
cd agents && adk web --port 8100

# Fix 4: Use explicit loading
from google.adk import dev
from clarifier.agent import root_agent
dev.run(agents=[root_agent], port=8100)
```

### Issue 2: Agent Execution Errors

**Problem**: Agent fails during execution

**Solution**:
```python
# Add error handling
try:
    result = agent.run(input_text)
except Exception as e:
    logger.error(f"Agent error: {e}")
    # Check Events tab for details
    # Review tool calls
    # Verify API keys
```

### Issue 3: Slow Response Times

**Problem**: Agents take too long to respond

**Solution**:
```python
# 1. Reduce max_output_tokens
agent = Agent(
    name="fast_agent",
    model="gemini-2.0-flash",
    max_output_tokens=500  # Limit output
)

# 2. Use caching
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query):
    return google_search(query)

# 3. Optimize prompts
instruction = """
Be concise. Limit responses to 3 bullet points.
"""
```

### Issue 4: Tool Integration Issues

**Problem**: Tools not working properly

**Solution**:
```python
# 1. Verify tool registration
agent = Agent(
    name="agent_with_tools",
    tools=[tool1, tool2]  # Must be tool objects
)

# 2. Check tool implementation
def my_tool(param1: str, param2: int = 10):
    """Tool description."""  # REQUIRED docstring
    return result

# 3. Monitor tool calls in Events tab
```

## Advanced Features

### 1. Custom Dev UI Configuration

```python
# custom_dev_ui.py
from google.adk import dev
from google.adk.dev import DevConfig

config = DevConfig(
    title="PresentationPro Development",
    description="Advanced presentation generation",
    theme="dark",
    enable_metrics=True,
    enable_tracing=True,
    enable_evaluation=True,
    custom_css="""
        .agent-selector {
            background: #192940;
            color: #73BF50;
        }
    """
)

dev.run(
    agents=agents,
    config=config,
    port=8100
)
```

### 2. Session Management

```python
# Enable session persistence
from google.adk.services import FileSessionService

session_service = FileSessionService(
    directory="./sessions",
    ttl_seconds=3600
)

dev.run(
    agents=agents,
    session_service=session_service,
    port=8100
)
```

### 3. Remote Dev UI

```python
# Enable remote access
dev.run(
    agents=agents,
    host="0.0.0.0",  # Allow external connections
    port=8100,
    auth_enabled=True,
    auth_token="secure_token_here"
)
```

### 4. Multi-Agent Coordination Testing

```python
# Test agent handoffs
from google.adk.agents import SequentialAgent

pipeline = SequentialAgent(
    name="test_pipeline",
    sub_agents=[clarifier, outline, slide_writer],
    pass_output=True
)

# Test in Dev UI with pipeline agent
dev.run(agents=[pipeline], port=8100)
```

### 5. Export Test Results

```python
# Export evaluation results
import json

def export_test_results(results):
    """Export test results to file."""

    output = {
        "timestamp": datetime.now().isoformat(),
        "agents_tested": len(results),
        "results": results,
        "summary": {
            "passed": sum(1 for r in results.values() if r["passed"]),
            "failed": sum(1 for r in results.values() if not r["passed"]),
            "average_score": sum(r["score"] for r in results.values()) / len(results)
        }
    }

    with open("test_results.json", "w") as f:
        json.dump(output, f, indent=2)
```

## Best Practices

### 1. Development Workflow

1. **Start Simple**: Test individual agents first
2. **Incremental Testing**: Add complexity gradually
3. **Monitor Events**: Always check Events tab
4. **Track Tokens**: Watch token usage
5. **Profile Performance**: Monitor response times

### 2. Agent Organization

```
agents/
├── core/              # Core functionality
│   ├── clarifier/
│   └── outline/
├── content/           # Content generation
│   ├── slide_writer/
│   └── notes_polisher/
├── quality/           # Quality control
│   ├── critic/
│   └── validator/
└── support/           # Support functions
    ├── research/
    └── design/
```

### 3. Testing Strategy

1. **Unit Tests**: Test each agent individually
2. **Integration Tests**: Test agent interactions
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Monitor latency and tokens
5. **Quality Tests**: Validate output quality

### 4. Debugging Tips

1. **Use Logging**: Add comprehensive logging
2. **Check Events**: Review execution traces
3. **Validate Inputs**: Ensure proper format
4. **Test Tools**: Verify tool functionality
5. **Monitor State**: Track state changes

## Conclusion

The ADK Dev UI is a powerful tool for developing and testing your presentation agents. Key points:

1. **Proper Structure**: Follow ADK conventions for agent discovery
2. **Testing**: Use Dev UI for interactive testing
3. **Debugging**: Leverage Events tab and traces
4. **Evaluation**: Build comprehensive test suites
5. **Optimization**: Monitor and improve performance

With proper setup and understanding of the Dev UI, you can efficiently develop, test, and deploy your presentation generation agents.