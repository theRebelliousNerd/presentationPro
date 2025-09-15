# CLAUDE.md - Orchestrate Agent (ADK/A2A Implementation)

## Agent Purpose & Responsibility

**Single Responsibility**: Central orchestrator that coordinates all presentation agents through the A2A protocol, managing the entire presentation creation workflow.

The Orchestrate agent is the **conductor** of the multi-agent system, routing tasks between specialized agents and managing the presentation pipeline.

### Core Function
- Coordinates multi-agent presentation workflows
- Routes tasks to appropriate specialized agents
- Manages agent communication via A2A protocol
- Tracks workflow state and progress
- Handles error recovery and retries
- Aggregates results from multiple agents

### Architecture Overview

This is NOT a typical ADK agent but rather a **host/orchestrator** that:
- Manages connections to remote A2A agents
- Implements task routing logic
- Maintains workflow state
- Handles parallel and sequential agent execution

## A2A Orchestration Architecture

### Framework Components

1. **Host Agent** (`agent.py`)
   ```python
   class HostAgent:
       def __init__(self):
           self.remote_connections = RemoteAgentConnections()
           self.card_resolver = A2ACardResolver()
   ```

2. **Remote Agent Connections** (`remote_agent_connection.py`)
   ```python
   class RemoteAgentConnections:
       async def send_to_agent(
           agent_name: str,
           message: SendMessageRequest,
           callback: TaskUpdateCallback
       )
   ```

3. **Agent Executor** (`agent_executor.py`)
   - Manages orchestration sessions
   - Coordinates agent interactions
   - Handles workflow execution

## File Structure

```
orchestrate/
├── __init__.py
├── agent.py                      # HostAgent orchestrator
├── agent_executor.py            # Workflow executor
├── remote_agent_connection.py  # A2A connection manager
├── ArangoClient.py             # Database session management
├── .env                        # Agent configuration
└── CLAUDE.md                   # This documentation
```

### Critical Files

1. **`agent.py`**
   - `HostAgent` class for orchestration
   - Task routing logic
   - Workflow management
   - Error handling

2. **`remote_agent_connection.py`**
   - A2A client connections
   - Agent discovery
   - Message routing
   - Response aggregation

3. **`agent_executor.py`**
   - Workflow execution engine
   - State management
   - Progress tracking

## Implementation Details

### Workflow Stages

1. **Clarification Phase**
   ```python
   # Route to Clarifier agent
   await send_to_agent("clarifier", clarify_request)
   ```

2. **Outline Generation**
   ```python
   # Route to Outline agent
   await send_to_agent("outline", outline_request)
   ```

3. **Slide Content Creation**
   ```python
   # Parallel execution for multiple slides
   tasks = [send_to_agent("slide_writer", slide) for slide in slides]
   await asyncio.gather(*tasks)
   ```

4. **Quality Assurance**
   ```python
   # Route to Critic agent
   await send_to_agent("critic", review_request)
   ```

5. **Enhancement Phase**
   ```python
   # Parallel enhancement agents
   await asyncio.gather(
       send_to_agent("notes_polisher", notes_request),
       send_to_agent("design", design_request),
       send_to_agent("script_writer", script_request)
   )
   ```

### Agent Registry

Configured agents and their roles:
- **clarifier**: Goal refinement
- **outline**: Structure generation
- **slide_writer**: Content creation
- **critic**: Quality assurance
- **notes_polisher**: Speaker notes enhancement
- **design**: Visual specifications
- **script_writer**: Full narrative
- **research**: Data gathering

### Error Handling

```python
try:
    response = await send_to_agent(agent_name, request)
except A2AConnectionError:
    # Retry logic or fallback
    response = await retry_with_backoff(...)
```

## Testing Requirements

### Integration Tests
```python
async def test_full_workflow():
    """Test complete presentation generation workflow."""
    host = HostAgent()
    
    # Start with user input
    initial_input = {"text": "Create a presentation about AI"}
    
    # Run through full pipeline
    result = await host.create_presentation(initial_input)
    
    assert result["status"] == "complete"
    assert "slides" in result
    assert len(result["slides"]) > 0
```

### Component Tests
- Agent connection establishment
- Message routing accuracy
- Parallel execution handling
- Error recovery mechanisms
- State persistence

## Configuration

### Environment Variables (.env)
```bash
# A2A Agent URLs
CLARIFIER_URL=http://localhost:10001
OUTLINE_URL=http://localhost:10002
SLIDE_WRITER_URL=http://localhost:10003
CRITIC_URL=http://localhost:10004
NOTES_POLISHER_URL=http://localhost:10005
DESIGN_URL=http://localhost:10006
SCRIPT_WRITER_URL=http://localhost:10007
RESEARCH_URL=http://localhost:10008

# Database
ARANGO_URL=http://localhost:8529

# API Keys
GOOGLE_GENAI_API_KEY=your_key_here
```

### Agent Discovery
The orchestrator can use:
- Static configuration (URLs in .env)
- Dynamic discovery via A2ACardResolver
- Service mesh integration

## Deployment Notes

### Running the Orchestrator
```bash
# Standalone orchestrator
python -m agents.orchestrate.agent

# With all agents
docker-compose up orchestrator clarifier outline slide_writer critic
```

### Container Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "agents.orchestrate.agent"]
```

### Scaling Considerations
- Orchestrator is typically singleton
- Individual agents can scale horizontally
- Use load balancing for agent pools
- Consider message queue for high volume

## Monitoring

### Key Metrics
- Workflow completion rate
- Average presentation generation time
- Agent response times
- Error rates by agent
- Retry counts
- Resource utilization

### Health Checks
- All agent connections alive
- Database connectivity
- API key validity
- Memory/CPU usage

## Troubleshooting

### Common Issues

1. **Agent Connection Failures**
   - Verify agent URLs in .env
   - Check network connectivity
   - Ensure agents are running

2. **Workflow Hangs**
   - Check for timeout configuration
   - Monitor agent response times
   - Look for deadlocks in parallel execution

3. **Inconsistent Results**
   - Verify agent versions match
   - Check for race conditions
   - Ensure proper state management

4. **Performance Issues**
   - Profile agent response times
   - Check for N+1 query problems
   - Consider caching frequently used data

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use environment variable
DEBUG=true python -m agents.orchestrate.agent
```

## Migration Notes

This orchestrator has been designed for the ADK/A2A architecture:
- Uses A2A protocol for all agent communication
- Implements modern async/await patterns
- Supports parallel agent execution
- Built-in retry and error handling

## Future Enhancements

Potential improvements:
- Dynamic workflow definitions
- Agent capability discovery
- Workflow versioning
- Real-time progress streaming
- Multi-tenant support
- Workflow templates
- Performance optimization through caching
- Advanced retry strategies
- Circuit breaker patterns
- Distributed tracing integration