# ADK Dev UI Integration Guide

## Overview

The ADK Dev UI has been successfully integrated into the presentation generation system, providing a powerful development and testing interface for all agents. This guide explains the architecture, usage, and migration path.

## What's New

### 1. ADK Framework Integration
- **Agent Registry**: Centralized registration system for all agents
- **Tool Decorators**: `@agent` and `@tool` decorators for clean agent definition
- **Discovery Mechanism**: Automatic agent discovery for Dev UI
- **Enhanced Telemetry**: Real-time token tracking and performance metrics

### 2. Dev UI Features
- **Web Interface**: Accessible at `http://localhost:8089/adk-dev`
- **Agent Testing**: Test individual agents in isolation
- **WebSocket Chat**: Real-time bidirectional communication
- **Telemetry Dashboard**: Monitor token usage and response times
- **Trace Logging**: Debug agent execution flow

### 3. Production API Compatibility
- All existing endpoints remain unchanged
- Dev UI runs alongside production API
- No breaking changes to frontend integration

## Architecture

```
adkpy/
├── adk/                          # ADK Framework (NEW)
│   ├── __init__.py              # Registry and decorators
│   ├── base_agent.py            # Enhanced BaseAgent class
│   └── dev_ui.py                # Dev UI server
├── agents/
│   ├── clarifier_agent.py       # Original agent (still works)
│   ├── clarifier_agent_v2.py    # ADK-enhanced version (NEW)
│   └── [other agents]
├── app/
│   └── main.py                  # Updated with Dev UI integration
└── test_adk_dev_ui.py          # Test suite (NEW)
```

## Quick Start

### 1. Start the Services

```bash
# Start all services including ADK backend
docker compose up --build adkpy arangodb

# Or start just the ADK backend
docker compose up --build adkpy
```

### 2. Access the Dev UI

Open your browser and navigate to:
```
http://localhost:8089/adk-dev
```

### 3. Test an Agent

1. Select an agent from the left panel
2. Type a message in the chat interface
3. Monitor telemetry in the right panel
4. View trace logs for debugging

### 4. Run Tests

```bash
# From the adkpy directory
python test_adk_dev_ui.py
```

## Agent Migration Guide

### Converting Existing Agents to ADK Pattern

#### Before (Original Pattern):
```python
class ClarifierAgent(BaseAgent):
    def run(self, data: Input) -> AgentResult:
        # Agent logic
        return AgentResult(...)
```

#### After (ADK Pattern):
```python
from adk import agent, tool
from adk.base_agent import BaseAgent

@agent(
    name="clarifier",
    version="2.0.0",
    description="Refines user goals through targeted questions",
    category="llm"
)
class ClarifierAgent(BaseAgent):

    @tool("analyze_context")
    def analyze_context(self, history, initial_input):
        # Tool logic
        pass

    def run(self, data: ClarifierInput) -> AgentResult:
        # Agent logic with tool calls
        context = self.call_tool("analyze_context", ...)
        return self.create_result(...)
```

### Key Benefits of Migration:
1. **Automatic Registration**: Agents are auto-discovered by Dev UI
2. **Tool Tracing**: All tool calls are tracked and logged
3. **Better Telemetry**: Enhanced token and cost tracking
4. **Dev UI Testing**: Test agents individually via chat interface
5. **Standardized Patterns**: Consistent structure across all agents

## API Endpoints

### Production Endpoints (Unchanged)
- `POST /v1/clarify` - Run clarification
- `POST /v1/outline` - Generate outline
- `POST /v1/slide/write` - Write slide content
- `GET /health` - Health check

### Dev UI Endpoints (New)
- `GET /adk-dev` - Dev UI interface
- `GET /adk-dev/api/agents` - List all agents
- `GET /adk-dev/api/agent/{id}` - Get agent details
- `POST /adk-dev/api/agent/{id}/chat` - Chat with agent
- `WS /adk-dev/ws/agent/{id}` - WebSocket connection

## Testing Workflow

### 1. Individual Agent Testing
Use the Dev UI to test each agent in isolation:
- Clarifier: Test question generation
- Outline: Test structure creation
- SlideWriter: Test content generation
- Critic: Test feedback quality

### 2. Integration Testing
Test the full workflow:
```python
# Use the test script
python test_adk_dev_ui.py

# Or manually via curl
curl -X POST http://localhost:8089/v1/clarify \
  -H "Content-Type: application/json" \
  -d '{"history": [], "initialInput": {"text": "AI presentation"}}'
```

### 3. Performance Testing
Monitor in Dev UI:
- Token usage per agent
- Response times
- Cost estimates
- Memory usage

## Troubleshooting

### Common Issues and Solutions

#### 1. Dev UI Not Loading
```bash
# Check if ADK backend is running
docker logs presentationpro-adkpy-1

# Verify port is accessible
curl http://localhost:8089/health
```

#### 2. Agent Not Appearing in Dev UI
```python
# Ensure agent is decorated
@agent(name="my_agent", version="1.0.0")
class MyAgent(BaseAgent):
    pass

# Check registration in logs
docker logs presentationpro-adkpy-1 | grep "Registered agent"
```

#### 3. WebSocket Connection Failed
```bash
# Check CORS settings in main.py
# Ensure WebSocket upgrade is allowed
# Verify firewall/proxy settings
```

## Migration Status

### Completed
- ✅ ADK framework setup
- ✅ Dev UI implementation
- ✅ Agent registry system
- ✅ WebSocket communication
- ✅ ClarifierAgent v2 (example migration)
- ✅ Test suite

### Pending
- ⏳ Migrate remaining 7 agents to ADK pattern
- ⏳ Playwright end-to-end tests
- ⏳ Performance optimization
- ⏳ Production deployment guide

## Best Practices

### 1. Agent Development
- Always use the `@agent` decorator
- Define clear input/output schemas
- Implement meaningful tool functions
- Add comprehensive examples

### 2. Testing
- Test agents individually first
- Use Dev UI for interactive debugging
- Monitor telemetry for optimization
- Write automated tests for critical paths

### 3. Performance
- Cache frequently used data
- Optimize prompt sizes
- Use appropriate models for each task
- Monitor token usage trends

## Next Steps

1. **Migrate Remaining Agents**: Convert all 8 agents to ADK pattern
2. **Enhance Dev UI**: Add more visualization features
3. **Create Playwright Tests**: Automated testing for both UIs
4. **Optimize Performance**: Profile and optimize slow operations
5. **Production Deployment**: Deploy with monitoring and alerting

## Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Python Repository](https://github.com/google/adk-python)
- [ADK Codelabs](https://codelabs.developers.google.com/your-first-agent-with-adk)
- [A2A Protocol Specification](./adkpy/a2a/README.md)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Docker logs: `docker logs presentationpro-adkpy-1`
3. Test with: `python test_adk_dev_ui.py`
4. Access Dev UI: http://localhost:8089/adk-dev

---

**Version**: 1.0.0
**Last Updated**: 2025-09-14
**Status**: Phase 1 Complete - Dev UI Integrated