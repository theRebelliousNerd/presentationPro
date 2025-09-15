# ADK Agent-to-Agent (A2A) Integration Guide

## Table of Contents
1. [Overview](#overview)
2. [A2A Protocol Fundamentals](#a2a-protocol-fundamentals)
3. [Setting Up A2A Server](#setting-up-a2a-server)
4. [Creating Agent Cards](#creating-agent-cards)
5. [A2A Client Implementation](#a2a-client-implementation)
6. [Orchestrator Pattern](#orchestrator-pattern)
7. [PresentationPro A2A Architecture](#presentationpro-a2a-architecture)
8. [Message Format and Schemas](#message-format-and-schemas)
9. [Error Handling and Retries](#error-handling-and-retries)
10. [Testing A2A Communication](#testing-a2a-communication)

## Overview

The Agent-to-Agent (A2A) protocol enables standardized communication between distributed AI agents. This allows agents to:
- Run on different infrastructure (Cloud Run, local servers, Agent Engine)
- Communicate asynchronously via HTTP/SSE
- Maintain independence while collaborating
- Scale horizontally across services

## A2A Protocol Fundamentals

### Core Concepts

1. **Agent Cards**: Metadata describing an agent's capabilities
2. **Message Protocol**: Standardized request/response format
3. **Server-Sent Events (SSE)**: Streaming responses for long-running tasks
4. **Orchestrator**: Central coordinator for multi-agent workflows

### Protocol Benefits

- **Decoupling**: Agents can run independently
- **Scalability**: Each agent can scale based on its workload
- **Flexibility**: Mix local and cloud-deployed agents
- **Standardization**: Common interface for all agents

## Setting Up A2A Server

### Basic A2A Server Wrapper

```python
# agents/clarifier/a2a_server.py
from google.adk.agents.a2a import A2AStarletteApplication, AgentCard
from starlette.applications import Starlette
from starlette.routing import Mount
from agent import root_agent  # Import your ADK agent

# Create Agent Card
clarifier_card = AgentCard(
    agent_id="clarifier_agent",
    name="Clarifier Agent",
    description="Refines presentation goals through targeted Q&A",
    input_schema={
        "type": "object",
        "properties": {
            "user_request": {"type": "string"},
            "context": {"type": "object"}
        },
        "required": ["user_request"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "questions": {"type": "array", "items": {"type": "string"}},
            "understanding_level": {"type": "number"}
        }
    }
)

# Create A2A Application
a2a_app = A2AStarletteApplication(
    agent=root_agent,
    agent_card=clarifier_card
)

# Create Starlette app with A2A mounted
app = Starlette(
    routes=[
        Mount("/", app=a2a_app)
    ]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10001)
```

### Running Multiple A2A Servers

```bash
# Start each agent on its designated port
python agents/clarifier/a2a_server.py      # Port 10001
python agents/outline/a2a_server.py        # Port 10002
python agents/slide_writer/a2a_server.py   # Port 10003
python agents/critic/a2a_server.py         # Port 10004
python agents/notes_polisher/a2a_server.py # Port 10005
python agents/design/a2a_server.py         # Port 10006
python agents/script_writer/a2a_server.py  # Port 10007
python agents/research/a2a_server.py       # Port 10008
```

## Creating Agent Cards

### Complete Agent Card Schema

```python
from google.adk.agents.a2a import AgentCard
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class PresentationAgentCard(AgentCard):
    """Extended agent card for presentation agents."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        capabilities: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        timeout_seconds: Optional[int] = 300
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema
        )
        self.capabilities = capabilities or []
        self.dependencies = dependencies or []
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds

# Example: Slide Writer Agent Card
slide_writer_card = PresentationAgentCard(
    agent_id="slide_writer_agent",
    name="Slide Writer",
    description="Generates detailed slide content with speaker notes",
    input_schema={
        "type": "object",
        "properties": {
            "outline": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "sections": {"type": "array"}
                }
            },
            "style_preferences": {"type": "object"},
            "target_audience": {"type": "string"}
        },
        "required": ["outline"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "slides": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "speaker_notes": {"type": "string"},
                        "visual_suggestions": {"type": "array"}
                    }
                }
            }
        }
    },
    capabilities=["content_generation", "note_creation", "visual_planning"],
    dependencies=["outline_agent"],
    max_tokens=4000,
    timeout_seconds=180
)
```

## A2A Client Implementation

### Basic A2A Client

```python
# agents/orchestrator/a2a_client.py
import httpx
import json
from typing import Dict, Any, Optional, AsyncIterator
import asyncio
from google.adk.agents import Agent

class A2AClient:
    """Client for communicating with A2A agents."""

    def __init__(self, base_url: str, timeout: int = 300):
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def get_agent_card(self) -> Dict[str, Any]:
        """Retrieve agent card from A2A server."""
        response = await self.client.get(f"{self.base_url}/agent-card")
        response.raise_for_status()
        return response.json()

    async def send_message(
        self,
        message: Dict[str, Any],
        stream: bool = True
    ) -> AsyncIterator[str]:
        """Send message to A2A agent and stream response."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json"
        }

        async with self.client.stream(
            "POST",
            f"{self.base_url}/message",
            json=message,
            headers=headers
        ) as response:
            response.raise_for_status()

            if stream:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            yield json.loads(data)
            else:
                yield response.json()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Usage example
async def call_clarifier_agent(user_request: str):
    """Example of calling the clarifier agent via A2A."""
    client = A2AClient("http://localhost:10001")

    try:
        # Get agent card
        card = await client.get_agent_card()
        print(f"Connected to: {card['name']}")

        # Send message
        message = {
            "user_request": user_request,
            "context": {"session_id": "abc123"}
        }

        # Stream response
        result = {}
        async for chunk in client.send_message(message):
            if "questions" in chunk:
                result["questions"] = chunk["questions"]
            if "understanding_level" in chunk:
                result["understanding_level"] = chunk["understanding_level"]

        return result

    finally:
        await client.close()
```

## Orchestrator Pattern

### Multi-Agent Orchestrator

```python
# agents/orchestrator/orchestrator_agent.py
from google.adk.agents import Agent, BaseAgent
from typing import Dict, Any, List, Optional
import asyncio
from a2a_client import A2AClient

class PresentationOrchestrator(BaseAgent):
    """Orchestrates multiple A2A agents for presentation generation."""

    def __init__(self):
        super().__init__(
            name="presentation_orchestrator",
            description="Coordinates multi-agent presentation generation"
        )

        # Agent endpoints
        self.agent_endpoints = {
            "clarifier": "http://localhost:10001",
            "outline": "http://localhost:10002",
            "slide_writer": "http://localhost:10003",
            "critic": "http://localhost:10004",
            "notes_polisher": "http://localhost:10005",
            "design": "http://localhost:10006",
            "script_writer": "http://localhost:10007",
            "research": "http://localhost:10008"
        }

        # Create clients
        self.clients = {
            name: A2AClient(url)
            for name, url in self.agent_endpoints.items()
        }

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the full presentation generation workflow."""

        # Phase 1: Clarification
        clarified = await self._clarify_request(state["user_request"])
        state["clarified_goals"] = clarified

        # Phase 2: Research (parallel with outline)
        research_task = asyncio.create_task(
            self._research_topic(clarified)
        )

        # Phase 3: Generate Outline
        outline = await self._generate_outline(clarified)
        state["outline"] = outline

        # Wait for research
        research_results = await research_task
        state["research"] = research_results

        # Phase 4: Generate Slides (parallel)
        slides = await self._generate_slides_parallel(
            outline,
            research_results
        )
        state["slides"] = slides

        # Phase 5: Critique and Polish (sequential)
        critiqued = await self._critique_slides(slides)
        polished = await self._polish_notes(critiqued)
        state["final_slides"] = polished

        # Phase 6: Design and Script (parallel)
        design_task = asyncio.create_task(
            self._create_design(polished)
        )
        script_task = asyncio.create_task(
            self._write_script(polished)
        )

        state["design"] = await design_task
        state["script"] = await script_task

        return state

    async def _clarify_request(
        self,
        user_request: str
    ) -> Dict[str, Any]:
        """Clarify user request using clarifier agent."""
        client = self.clients["clarifier"]

        result = {}
        async for chunk in client.send_message({
            "user_request": user_request
        }):
            result.update(chunk)

        return result

    async def _generate_slides_parallel(
        self,
        outline: Dict[str, Any],
        research: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate slides in parallel for each section."""
        client = self.clients["slide_writer"]

        # Create tasks for each section
        tasks = []
        for section in outline["sections"]:
            task = client.send_message({
                "section": section,
                "research": research.get(section["title"], {}),
                "style": outline.get("style", {})
            })
            tasks.append(task)

        # Wait for all slides
        slides = []
        for task in asyncio.as_completed(tasks):
            result = {}
            async for chunk in task:
                result.update(chunk)
            slides.append(result)

        return slides

    async def cleanup(self):
        """Close all client connections."""
        for client in self.clients.values():
            await client.close()

# Create root agent
orchestrator = PresentationOrchestrator()
root_agent = orchestrator
```

## PresentationPro A2A Architecture

### Recommended Architecture

```
┌─────────────────────────────────────────────────┐
│              FastAPI Backend (8089)              │
│                  Orchestrator                    │
└────────────┬────────────────────────────────────┘
             │ A2A Protocol (HTTP/SSE)
    ┌────────┴────────┬──────────┬──────────┐
    │                 │          │          │
┌───▼───┐      ┌──────▼───┐ ┌───▼───┐ ┌───▼───┐
│Clarify│      │ Outline  │ │Writer │ │Critic │
│ 10001 │      │  10002   │ │ 10003 │ │ 10004 │
└───────┘      └──────────┘ └───────┘ └───────┘
    │                 │          │          │
┌───▼───┐      ┌──────▼───┐ ┌───▼───┐ ┌───▼───┐
│Polish │      │  Design  │ │Script │ │Search │
│ 10005 │      │  10006   │ │ 10007 │ │ 10008 │
└───────┘      └──────────┘ └───────┘ └───────┘
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  orchestrator:
    build: ./adkpy
    ports:
      - "8089:8089"
    environment:
      - GOOGLE_GENAI_API_KEY=${GOOGLE_GENAI_API_KEY}
    depends_on:
      - clarifier
      - outline
      - slide_writer
      - critic

  clarifier:
    build: ./adkpy/agents/clarifier
    ports:
      - "10001:10001"
    environment:
      - GOOGLE_GENAI_API_KEY=${GOOGLE_GENAI_API_KEY}
      - PORT=10001

  outline:
    build: ./adkpy/agents/outline
    ports:
      - "10002:10002"
    environment:
      - GOOGLE_GENAI_API_KEY=${GOOGLE_GENAI_API_KEY}
      - PORT=10002

  # ... other agents ...
```

## Message Format and Schemas

### Standard A2A Message Format

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class A2AMessage(BaseModel):
    """Standard A2A message format."""

    # Message metadata
    message_id: str
    timestamp: datetime
    agent_id: str
    session_id: Optional[str] = None

    # Message content
    action: str  # "execute", "query", "stream"
    payload: Dict[str, Any]

    # Context and tracing
    context: Optional[Dict[str, Any]] = None
    parent_message_id: Optional[str] = None
    trace_id: Optional[str] = None

    # Response preferences
    streaming: bool = True
    timeout_seconds: int = 300
    max_retries: int = 3

class A2AResponse(BaseModel):
    """Standard A2A response format."""

    # Response metadata
    message_id: str
    response_to: str
    timestamp: datetime
    agent_id: str

    # Response content
    status: str  # "success", "error", "partial"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    # Performance metrics
    processing_time_ms: int
    tokens_used: Optional[int] = None

    # Streaming support
    is_final: bool = True
    chunk_index: Optional[int] = None
```

### PresentationPro Message Examples

```python
# Clarifier Request
clarifier_request = A2AMessage(
    message_id="msg_001",
    timestamp=datetime.now(),
    agent_id="orchestrator",
    session_id="session_abc",
    action="clarify",
    payload={
        "user_request": "Create a presentation about AI safety",
        "target_audience": "executives",
        "duration": 20,
        "style": "professional"
    },
    context={
        "user_id": "user_123",
        "presentation_id": "pres_456"
    }
)

# Slide Writer Request
slide_writer_request = A2AMessage(
    message_id="msg_002",
    timestamp=datetime.now(),
    agent_id="orchestrator",
    session_id="session_abc",
    action="generate_slides",
    payload={
        "outline": {
            "title": "AI Safety in the Enterprise",
            "sections": [
                {
                    "title": "Introduction",
                    "points": ["What is AI Safety", "Why it matters"]
                },
                {
                    "title": "Current Challenges",
                    "points": ["Alignment", "Robustness", "Interpretability"]
                }
            ]
        },
        "research_data": {...},
        "visual_style": "modern"
    },
    parent_message_id="msg_001",
    streaming=True
)
```

## Error Handling and Retries

### Robust A2A Client with Retries

```python
import asyncio
from typing import Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

class RobustA2AClient:
    """A2A client with error handling and retries."""

    def __init__(
        self,
        base_url: str,
        max_retries: int = 3,
        timeout: int = 300
    ):
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))
    )
    async def send_message_with_retry(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send message with automatic retries."""
        try:
            response = await self.client.post(
                f"{self.base_url}/message",
                json=message
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                # Service unavailable, retry
                raise
            elif e.response.status_code == 429:
                # Rate limited, wait and retry
                await asyncio.sleep(5)
                raise
            else:
                # Other HTTP errors, don't retry
                return {
                    "status": "error",
                    "error": f"HTTP {e.response.status_code}: {e.response.text}"
                }

        except httpx.TimeoutException:
            # Timeout, will retry
            raise

        except Exception as e:
            # Unexpected error
            return {
                "status": "error",
                "error": f"Unexpected error: {str(e)}"
            }

    async def health_check(self) -> bool:
        """Check if agent is healthy."""
        try:
            response = await self.client.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
```

### Circuit Breaker Pattern

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker for A2A communication."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try again."""
        return (
            self.last_failure_time and
            datetime.now() - self.last_failure_time >
            timedelta(seconds=self.recovery_timeout)
        )

    def _on_success(self):
        """Reset circuit breaker on success."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Record failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

## Testing A2A Communication

### Unit Test for A2A Server

```python
# tests/test_a2a_server.py
import pytest
import httpx
from fastapi.testclient import TestClient
from agents.clarifier.a2a_server import app

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

def test_agent_card_endpoint(client):
    """Test agent card retrieval."""
    response = client.get("/agent-card")
    assert response.status_code == 200

    card = response.json()
    assert card["agent_id"] == "clarifier_agent"
    assert "input_schema" in card
    assert "output_schema" in card

@pytest.mark.asyncio
async def test_message_endpoint(client):
    """Test message processing."""
    message = {
        "user_request": "Create a presentation about AI",
        "context": {"session_id": "test"}
    }

    response = client.post(
        "/message",
        json=message,
        headers={"Accept": "application/json"}
    )

    assert response.status_code == 200
    result = response.json()
    assert "questions" in result
    assert "understanding_level" in result
```

### Integration Test for Multi-Agent Flow

```python
# tests/test_integration.py
import asyncio
import pytest
from agents.orchestrator.orchestrator_agent import PresentationOrchestrator

@pytest.mark.asyncio
async def test_full_presentation_flow():
    """Test complete presentation generation flow."""

    # Start all A2A servers (in test fixtures)
    orchestrator = PresentationOrchestrator()

    try:
        # Initial state
        state = {
            "user_request": "Create a 10-slide presentation about renewable energy",
            "preferences": {
                "style": "modern",
                "audience": "general public"
            }
        }

        # Run orchestration
        result = await orchestrator.run(state)

        # Verify results
        assert "clarified_goals" in result
        assert "outline" in result
        assert "slides" in result
        assert "final_slides" in result
        assert "design" in result
        assert "script" in result

        # Check slide structure
        slides = result["final_slides"]
        assert len(slides) >= 10

        for slide in slides:
            assert "title" in slide
            assert "content" in slide
            assert "speaker_notes" in slide

    finally:
        await orchestrator.cleanup()
```

### Load Testing

```python
# tests/test_load.py
import asyncio
import time
from typing import List
import httpx

async def send_request(client: httpx.AsyncClient, index: int):
    """Send a single request."""
    start = time.time()

    try:
        response = await client.post(
            "http://localhost:10001/message",
            json={
                "user_request": f"Test request {index}",
                "context": {"test_id": index}
            },
            timeout=30
        )
        response.raise_for_status()
        duration = time.time() - start
        return {"success": True, "duration": duration, "index": index}

    except Exception as e:
        duration = time.time() - start
        return {"success": False, "duration": duration, "error": str(e)}

async def load_test(num_requests: int = 100, concurrent: int = 10):
    """Run load test against A2A server."""
    async with httpx.AsyncClient() as client:
        # Create tasks in batches
        results = []

        for i in range(0, num_requests, concurrent):
            batch = [
                send_request(client, j)
                for j in range(i, min(i + concurrent, num_requests))
            ]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)

        # Analyze results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        if successful:
            avg_duration = sum(r["duration"] for r in successful) / len(successful)
            max_duration = max(r["duration"] for r in successful)
            min_duration = min(r["duration"] for r in successful)

            print(f"Load Test Results:")
            print(f"  Total Requests: {num_requests}")
            print(f"  Successful: {len(successful)}")
            print(f"  Failed: {len(failed)}")
            print(f"  Avg Duration: {avg_duration:.2f}s")
            print(f"  Max Duration: {max_duration:.2f}s")
            print(f"  Min Duration: {min_duration:.2f}s")

        return results

if __name__ == "__main__":
    asyncio.run(load_test(num_requests=100, concurrent=10))
```

## Best Practices

### 1. Agent Independence
- Each agent should be self-contained
- Avoid tight coupling between agents
- Use message-based communication only

### 2. Error Resilience
- Implement retries with exponential backoff
- Use circuit breakers for failing services
- Provide fallback responses

### 3. Performance Optimization
- Stream responses for long-running tasks
- Implement caching where appropriate
- Use connection pooling for HTTP clients

### 4. Monitoring and Logging
- Log all A2A communications
- Track latency and error rates
- Implement health check endpoints

### 5. Security
- Validate all incoming messages
- Use authentication tokens for production
- Implement rate limiting

## Deployment Considerations

### Cloud Run Deployment

```yaml
# cloudbuild.yaml
steps:
  # Build clarifier agent
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/clarifier-agent', './agents/clarifier']

  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'clarifier-agent'
      - '--image=gcr.io/$PROJECT_ID/clarifier-agent'
      - '--region=us-central1'
      - '--platform=managed'
      - '--port=10001'
      - '--allow-unauthenticated'
      - '--set-env-vars=GOOGLE_GENAI_API_KEY=${_GOOGLE_GENAI_API_KEY}'
```

### Agent Engine Deployment

```python
# deploy_to_agent_engine.py
from google.cloud import aiplatform

# Initialize Vertex AI
aiplatform.init(project="your-project", location="us-central1")

# Deploy agent to Agent Engine
agent = aiplatform.Agent.create(
    display_name="clarifier-agent",
    agent_type="CUSTOM",
    agent_config={
        "image_uri": "gcr.io/your-project/clarifier-agent",
        "port": 10001,
        "environment_variables": {
            "GOOGLE_GENAI_API_KEY": "your-key"
        }
    }
)

print(f"Agent deployed: {agent.resource_name}")
```

## Next Steps

1. Implement A2A servers for all agents
2. Create comprehensive orchestrator
3. Add monitoring and logging
4. Deploy to Cloud Run or Agent Engine
5. Implement authentication and security
6. Add performance optimizations