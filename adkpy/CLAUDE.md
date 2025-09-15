# CLAUDE.md - ADK/A2A Architecture Guide

This file provides comprehensive architectural guidance for the ADK/A2A multi-agent presentation system. **This is the primary reference document for maintaining architectural integrity.**

## 🏗️ Architectural Overview

### System Design Principles

1. **Protocol-First Architecture**: Every agent interaction follows either A2A (agent-to-agent) or MCP (model context protocol)
2. **Service Isolation**: Each agent runs as an independent service with its own port
3. **Stateless Communication**: No shared state between agents; all context passed explicitly
4. **Fail-Safe Design**: Agent failures don't cascade; orchestrator handles retries
5. **Type Safety**: Pydantic models enforce data contracts at every boundary

### Protocol Usage

**A2A Protocol (Agent-to-Agent)**
- Used for: Inter-agent communication
- Format: JSON-RPC 2.0 over HTTP
- Ports: 10001-10008 (agent services)
- Version: 0.2.6

**MCP Protocol (Model Context Protocol)**
- Used for: Tool access (web search, RAG, vision)
- Format: JSON-RPC 2.0 over HTTP
- Port: 8090 (MCP server)
- Version: 2024-11-05

### Agent Communication Patterns

```
Frontend → Orchestrator (8088/8089) → Agent Network
                ↓
    ┌───────────┴─────────────┐
    │                         │
    ↓                         ↓
Agent Services            MCP Server (8090)
(10001-10008)                 ↓
    ↓                    Tool Services
A2A Protocol             (RAG, Search, Vision)
```

### Service Discovery

Agents register themselves via:
1. **Agent Cards**: Self-describing metadata (name, skills, capabilities)
2. **Health Endpoints**: `/health` for liveness checks
3. **Static Configuration**: Docker service names as hostnames

## 📁 Directory Structure

```
adkpy/
├── agents/              # Individual A2A agent services
│   ├── base/           # Shared base classes for all agents
│   ├── clarifier/      # Goal refinement agent (port 10001)
│   ├── outline/        # Presentation structure agent (port 10002)
│   ├── slide_writer/   # Content generation agent (port 10003)
│   ├── critic/         # Quality review agent (port 10004)
│   ├── notes_polisher/ # Speaker notes agent (port 10005)
│   ├── design/         # Visual design agent (port 10006)
│   ├── script_writer/  # Script generation agent (port 10007)
│   └── research/       # Background research agent (port 10008)
├── tools/              # MCP server and tool implementations
│   └── mcp_server/     # Centralized MCP server
├── protocols/          # Protocol type definitions
│   ├── a2a_types.py    # A2A protocol models
│   └── mcp_types.py    # MCP protocol models
├── shared/             # Shared utilities
│   ├── schemas.py      # Common data models
│   ├── telemetry.py    # Usage tracking
│   └── config.py       # Configuration management
├── orchestrator/       # Main orchestration service
│   └── main.py         # FastAPI orchestrator (port 8088/8089)
├── app/               # Legacy compatibility layer
│   └── main.py        # Monolithic FastAPI (being phased out)
└── base/              # Infrastructure components
```

## 🚀 Development Guidelines

### How to Add New Agents

1. **Create Agent Directory Structure**:
```bash
agents/new_agent/
├── __init__.py
├── agent.py           # Agent definition with Input/Output schemas
├── agent_executor.py  # Business logic implementation
├── a2a_server.py     # A2A protocol server
└── Dockerfile        # Container definition
```

2. **Define Agent Contract** (`agent.py`):
```python
from pydantic import BaseModel, Field
from typing import Dict, Any

class NewAgentInput(BaseModel):
    """Input schema for NewAgent."""
    data: str = Field(description="Input data")

class NewAgentOutput(BaseModel):
    """Output schema for NewAgent."""
    result: str = Field(description="Processed result")

class NewAgent:
    """Agent definition."""
    name = "NewAgent"
    version = "1.0.0"
    description = "Does something new"
```

3. **Implement Business Logic** (`agent_executor.py`):
```python
from ..base.agent_executor_base import AgentExecutorBase
from .agent import NewAgentInput, NewAgentOutput

class NewAgentExecutor(AgentExecutorBase):
    async def execute(self, input_data: NewAgentInput) -> NewAgentOutput:
        # Your agent logic here
        return NewAgentOutput(result="processed")
```

4. **Setup A2A Server** (`a2a_server.py`):
```python
from ..base.a2a_base import A2AServer, AgentCard, AgentSkill
from .agent_executor import NewAgentExecutor

class NewAgentA2AServer(A2AServer):
    def __init__(self, llm, host="0.0.0.0", port=10009):
        agent_card = AgentCard(
            name="NewAgent",
            version="1.0.0",
            description="Does something new",
            url=f"http://{host}:{port}",
            skills=[...]  # Define skills
        )
        executor = NewAgentExecutor(llm=llm)
        super().__init__(agent_card=agent_card, executor=executor)
```

5. **Add to Docker Compose**:
```yaml
new-agent:
  build:
    context: ./agents/new_agent
    dockerfile: Dockerfile
  container_name: presentationpro-new-agent
  environment:
    - PORT=10009
    - GOOGLE_GENAI_API_KEY=${GOOGLE_GENAI_API_KEY}
  networks:
    - presentation-network
```

### Protocol Compliance Requirements

**A2A Protocol MUST**:
- Use JSON-RPC 2.0 format
- Include proper request IDs
- Return structured errors with codes
- Support health checks at `/health`
- Provide agent card at `/agent/info`

**MCP Protocol MUST**:
- Follow MCP schema definitions
- Handle tool calls atomically
- Return proper error objects
- Support resource subscriptions

### Testing Strategies

1. **Unit Tests**: Test executors in isolation
2. **Protocol Tests**: Validate A2A/MCP compliance
3. **Integration Tests**: Test agent chains
4. **Load Tests**: Verify concurrent task handling

Example test structure:
```python
async def test_agent_a2a_compliance():
    """Test A2A protocol compliance."""
    server = AgentA2AServer(...)

    # Test health endpoint
    response = await server.health()
    assert response.status == "healthy"

    # Test task execution
    task = TaskRequest(...)
    result = await server.execute_task(task)
    assert result.status == "completed"
```

### Error Handling Patterns

```python
# Always use structured errors
from protocols.a2a_types import A2AError, A2AErrorCode

try:
    result = await execute_task(input_data)
except ValidationError as e:
    return A2AError(
        code=A2AErrorCode.INVALID_PARAMS,
        message="Invalid input parameters",
        data={"validation_errors": e.errors()}
    )
except TimeoutError:
    return A2AError(
        code=A2AErrorCode.TASK_TIMEOUT,
        message="Task execution timeout",
        data={"timeout_seconds": 300}
    )
```

## 🔧 Maintenance Rules

### Code Organization Standards

1. **One Agent, One Service**: Never combine agents in a single service
2. **Shared Code in `/shared`**: Common utilities go in shared module
3. **Protocol Types in `/protocols`**: All type definitions centralized
4. **Base Classes in `/agents/base`**: Inherit, don't duplicate

### Dependency Management

```python
# Good: Use shared dependencies
from shared.schemas import PresentationOutline
from protocols.a2a_types import TaskRequest

# Bad: Copy-paste code between agents
class MyOwnTaskRequest:  # Don't do this!
    pass
```

### Version Compatibility

- **Protocol Versions**: Check compatibility in agent cards
- **Schema Evolution**: Use optional fields for backward compatibility
- **Breaking Changes**: Bump major version, update all consumers

### Breaking Change Procedures

1. **Announce**: Document in CHANGELOG.md
2. **Deprecate**: Mark old endpoints/fields as deprecated
3. **Migrate**: Update all consumers
4. **Remove**: After grace period (2 releases)

## ⚠️ Critical Warnings

### What NOT to Do

❌ **Never Share State Between Agents**
```python
# BAD: Shared global state
GLOBAL_CACHE = {}  # Don't do this!

# GOOD: Pass context explicitly
async def execute(self, input_data, context):
    pass
```

❌ **Never Skip Protocol Validation**
```python
# BAD: Direct HTTP calls
response = requests.post(url, json=data)

# GOOD: Use protocol clients
from ..base.remote_connection import RemoteAgentConnection
agent = RemoteAgentConnection(url)
response = await agent.send_task(task)
```

❌ **Never Hardcode Service URLs**
```python
# BAD: Hardcoded URLs
url = "http://localhost:10001"

# GOOD: Use environment/config
url = os.getenv("CLARIFIER_URL", "http://clarifier:10001")
```

### Common Pitfalls

1. **Circular Dependencies**: Agents calling each other in loops
2. **Synchronous Blocking**: Not using async properly
3. **Memory Leaks**: Not cleaning up sessions
4. **Port Conflicts**: Using occupied ports

### Security Considerations

- **API Keys**: Never log or expose API keys
- **Input Validation**: Always validate with Pydantic
- **Rate Limiting**: Implement per-agent limits
- **Authentication**: Use bearer tokens for production

### Performance Gotchas

- **N+1 Queries**: Batch agent calls when possible
- **Large Payloads**: Stream or paginate large results
- **Connection Pools**: Reuse HTTP connections
- **Timeout Cascades**: Set appropriate timeouts

## 📋 Quick Reference

### Port Assignments

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Orchestrator | 8088/8089 | HTTP/REST | Main API gateway |
| MCP Server | 8090 | MCP | Tool access |
| Clarifier | 10001 | A2A | Goal refinement |
| Outline | 10002 | A2A | Structure planning |
| SlideWriter | 10003 | A2A | Content generation |
| Critic | 10004 | A2A | Quality review |
| NotesPolisher | 10005 | A2A | Speaker notes |
| Design | 10006 | A2A | Visual design |
| ScriptWriter | 10007 | A2A | Script generation |
| Research | 10008 | A2A | Background research |
| ArangoDB | 8530 | HTTP | Graph database |

### Environment Variables

```bash
# Required
GOOGLE_GENAI_API_KEY=your_key_here

# Service URLs (Docker networking)
ORCHESTRATOR_URL=http://orchestrator:8088
MCP_SERVER_URL=http://mcp-server:8090

# Agent Model Configuration
CLARIFIER_MODEL=googleai/gemini-2.5-flash
OUTLINE_MODEL=googleai/gemini-2.5-flash
SLIDE_WRITER_MODEL=googleai/gemini-2.5-flash
CRITIC_MODEL=googleai/gemini-2.5-flash
NOTES_MODEL=googleai/gemini-2.5-flash
DESIGN_MODEL=googleai/gemini-2.5-flash
SCRIPT_MODEL=googleai/gemini-2.5-flash
RESEARCH_MODEL=googleai/gemini-2.5-flash

# Optional
BING_SEARCH_API_KEY=...
ARANGO_ROOT_PASSWORD=root
```

### Docker Commands

```bash
# Build all services
docker compose build

# Start distributed system
docker compose up -d

# View logs for specific agent
docker logs -f presentationpro-clarifier

# Restart single agent
docker compose restart clarifier

# Scale agents (for load balancing)
docker compose up -d --scale slide-writer=3

# Clean shutdown
docker compose down

# Full reset (including volumes)
docker compose down -v
```

### Debugging Tips

1. **Check Agent Health**:
```bash
curl http://localhost:10001/health
```

2. **View Agent Card**:
```bash
curl http://localhost:10001/agent/info
```

3. **Monitor A2A Traffic**:
```bash
docker logs -f presentationpro-orchestrator | grep "A2A"
```

4. **Test MCP Tools**:
```bash
curl -X POST http://localhost:8090 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

5. **Debug Orchestration Flow**:
```python
# Enable debug logging in orchestrator
logging.getLogger("orchestrator").setLevel(logging.DEBUG)
```

## 🎯 Architecture Goals

The distributed A2A architecture enables:

1. **Scalability**: Scale individual agents based on load
2. **Resilience**: Isolate failures to single agents
3. **Flexibility**: Mix and match agent implementations
4. **Observability**: Track each agent's performance
5. **Maintainability**: Clear separation of concerns

Remember: **The architecture is the product.** Every line of code should respect the protocol boundaries and maintain the system's distributed nature.

## 📚 References

- [A2A Protocol Spec](protocols/a2a_types.py)
- [MCP Protocol Spec](protocols/mcp_types.py)
- [Google ADK Documentation](https://ai.google.dev/adk)
- [InstaVibe Reference Implementation](agents/instavideExamples/)

---

*Last Updated: 2025-01-14*
*Maintained by: ADK Solutions Architect*