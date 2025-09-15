# CLAUDE.md - Clarifier Agent (ADK/A2A Implementation)

## Agent Purpose & Responsibility

**Single Responsibility**: Drives a short, targeted Q&A to refine vague user presentation requests into clear, structured goals.

The Clarifier agent is the **first agent** in the presentation creation pipeline. It transforms ambiguous user input into precise specifications that downstream agents can work with effectively.

### Core Function
- Analyzes initial user requests and conversation history
- Asks **one single, targeted question** per interaction to gather missing information
- Identifies gaps in: audience, length, tone, required topics, success metrics
- Provides comprehensive goal summaries when sufficient information is gathered
- Sets `finished: true` only when goals are clear enough for the outline agent

### Input/Output Contracts

**Input** (JSON):
```json
{
    "history": [{"role": "user", "content": "..."}, ...],
    "initialInput": {"text": "...", "audience": "...", ...},
    "newFiles": [{"name": "...", "content": "..."}]
}
```

**Output** (JSON):
```json
{
    "response": "Either clarifying question OR final goal summary",
    "finished": false  // true only when ready for outline agent
}
```

## ADK/A2A Architecture

### Framework Components
This agent uses Google's ADK (Agent Development Kit) and A2A (Agent-to-Agent) protocol:

1. **ADK Agent** (`agent.py`)
   ```python
   from google.adk.agents import Agent
   
   root_agent = Agent(
       name="clarifier",
       model="gemini-2.0-flash-exp",
       description="Refines presentation goals through targeted Q&A",
       instruction="..."  # Full prompt template
   )
   ```

2. **A2A Executor** (`agent_executor.py`)
   ```python
   from a2a.server.agent_execution import AgentExecutor
   from google.adk import Runner
   
   class ClarifierAgentExecutor(AgentExecutor):
       def __init__(self, runner: Runner, card: AgentCard):
           self.runner = runner
           self._card = card
   ```

3. **A2A Server** (`a2a_server.py`)
   - Handles A2A protocol communication
   - Manages agent lifecycle
   - Provides health endpoints

### Port Assignment
- **Default Port**: Dynamically assigned by A2A
- **Health Check**: Via A2A server endpoints
- **Discovery**: Through A2A agent registry

## File Structure

```
clarifier/
├── __init__.py              # Module initialization
├── agent.py                 # ADK Agent definition
├── agent_executor.py        # A2A AgentExecutor implementation
├── a2a_server.py           # A2A protocol server (if standalone)
├── ArangoClient.py         # Database session management
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container configuration (if needed)
└── CLAUDE.md              # This documentation
```

### Critical Files

1. **`agent.py`**
   - ADK `Agent` instance with model and instructions
   - Defines the core clarification logic via prompts
   - JSON response format specification

2. **`agent_executor.py`**
   - Inherits from A2A's `AgentExecutor`
   - Implements `_process_request()` for task handling
   - Manages sessions via ADK's Runner
   - Handles error recovery and logging

3. **`a2a_server.py`** (if running standalone)
   - A2A server setup and configuration
   - Agent card registration
   - Protocol endpoint handlers

## Implementation Details

### ADK Agent Definition
```python
root_agent = Agent(
    name="clarifier",
    model="gemini-2.0-flash-exp",
    description="Refines presentation goals through targeted Q&A",
    instruction="""You are a Clarifier agent...
    
    Input Format:
    - history: Conversation array
    - initialInput: Original request
    - newFiles: Optional uploads
    
    Output Format:
    {
        "response": "question or summary",
        "finished": boolean
    }
    """
)
```

### A2A Executor Pattern
```python
class ClarifierAgentExecutor(AgentExecutor):
    async def _process_request(
        self,
        new_message: types.Content,
        session_id: str,
        task_updater: TaskUpdater,
    ) -> None:
        # Get or create session
        session_obj = await self._upsert_session(session_id)
        
        # Process with ADK runner
        async for chunk in self.runner.run_stream(session_obj, new_message):
            if chunk.text:
                await task_updater.send_text_update(chunk.text)
```

### Session Management
Uses ADK's built-in session management:
- Sessions persist across interactions
- Context maintained automatically
- ArangoClient provides custom session storage if needed

## Testing Requirements

### Unit Tests
```python
async def test_clarifier_with_adk():
    """Test clarifier using ADK runner."""
    runner = Runner(agent=root_agent)
    session = await runner.create_session()
    
    message = types.Content(
        parts=[types.Part(text=json.dumps({
            "history": [],
            "initialInput": {"text": "Make a presentation"},
            "newFiles": None
        }))]
    )
    
    response = await runner.run(session, message)
    result = json.loads(response.text)
    assert not result["finished"]
    assert "?" in result["response"]
```

### Integration Tests
- A2A protocol compliance
- Multi-agent communication with outline agent
- Session persistence across requests
- Error handling and recovery

### Performance Benchmarks
- **Response Time**: < 3 seconds via ADK
- **Token Usage**: Tracked via ADK telemetry
- **Concurrent Sessions**: Handled by ADK Runner
- **Memory**: Managed by ADK framework

## Common Modifications

### Updating the Prompt
**Location**: `agent.py` - `instruction` parameter
```python
root_agent = Agent(
    name="clarifier",
    model="gemini-2.0-flash-exp",
    instruction="Updated prompt here..."
)
```

### Changing the Model
```python
root_agent = Agent(
    name="clarifier",
    model="gemini-2.0-flash-thinking-exp",  # Or other model
    ...
)
```

### Adding Tools
ADK supports tool integration:
```python
from google.adk.tools import Tool

search_tool = Tool(...)
root_agent = Agent(
    name="clarifier",
    tools=[search_tool],
    ...
)
```

## Agent-Specific Warnings

### ⚠️ What Breaks This Agent

1. **JSON Response Corruption**
   - Symptom: Parser errors in downstream processing
   - Cause: Model deviates from JSON format
   - Fix: Strengthen JSON instructions in prompt

2. **Session Loss**
   - Symptom: Context lost between interactions
   - Cause: Session ID mismatch or timeout
   - Fix: Ensure consistent session_id usage

3. **Token Limit Exceeded**
   - Symptom: Truncated responses or errors
   - Cause: Long conversation histories
   - Fix: Implement conversation summarization

### Critical Dependencies
- **Google ADK**: Core agent framework
- **A2A Protocol**: Agent communication layer
- **Gemini API**: LLM backend (via ADK)
- **ArangoDB**: Optional session persistence

### Performance Considerations
- ADK handles rate limiting automatically
- Sessions cached by Runner for efficiency
- Streaming responses reduce latency
- Token usage tracked for billing

## Pipeline Integration

### Communication Flow
```
User → Frontend → Orchestrator → A2A Protocol → Clarifier
                                      ↓
                              ADK Runner & Session
                                      ↓
                               Gemini Model
```

### State Management
- Session state maintained by ADK
- Conversation history in session context
- Output passed to outline agent when `finished: true`

### A2A Protocol Details
- Agent registered with A2A server
- Tasks received via A2A protocol
- Results returned through task updater
- Health monitoring via A2A endpoints

## Deployment Notes

### Running Standalone
```bash
# With A2A server
python -m agents.clarifier.a2a_server

# Or integrated with orchestrator
# (Orchestrator manages agent lifecycle)
```

### Environment Variables
```bash
GOOGLE_GENAI_API_KEY=your_key_here
ARANGO_URL=http://localhost:8529  # Optional
```

### Container Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "agents.clarifier.a2a_server"]
```

### Monitoring
- ADK provides built-in telemetry
- A2A server exposes health endpoints
- Token usage tracked automatically
- Session metrics available via ADK

## Troubleshooting

### Common Issues

1. **"Agent not found" errors**
   - Check A2A server registration
   - Verify agent name matches

2. **Session errors**
   - Ensure Runner properly initialized
   - Check session ID format

3. **Response parsing failures**
   - Validate JSON output format
   - Check model instruction adherence

4. **Performance degradation**
   - Monitor token usage
   - Check session cache efficiency
   - Review conversation length

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Migration Notes

This agent has been migrated from custom base classes to ADK/A2A:
- Previous: Inherited from `BaseAgent` and `BaseAgentExecutor`
- Current: Uses ADK `Agent` and A2A `AgentExecutor`
- Benefits: Better performance, built-in session management, automatic telemetry