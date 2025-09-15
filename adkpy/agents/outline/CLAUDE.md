# CLAUDE.md - Outline Agent (ADK/A2A Implementation)

## Agent Purpose & Responsibility

**Single Responsibility**: Transforms clarified presentation goals into a structured, logical slide outline with 6-12 concise titles.

The Outline agent is the **second agent** in the presentation pipeline, receiving clarified goals from the Clarifier and producing a presentation structure for the Slide Writer.

### Core Function
- Analyzes clarified presentation requirements
- Creates logical flow from introduction to conclusion
- Generates 6-12 action-oriented slide titles
- Ensures each title is specific and meaningful (4-8 words)
- Respects constraints like slide count and duration

### Input/Output Contracts

**Input** (JSON):
```json
{
    "clarifiedContent": "Clear presentation goals and key messages",
    "constraints": {
        "max_slides": 10,
        "duration": "30 minutes"
    }
}
```

**Output** (JSON):
```json
{
    "outline": [
        "Title 1: Introduction and Overview",
        "Title 2: Problem Statement",
        "Title 3: Proposed Solution",
        "Final Title: Conclusion and Next Steps"
    ]
}
```

## ADK/A2A Architecture

### Framework Components
This agent uses Google's ADK (Agent Development Kit) and A2A (Agent-to-Agent) protocol:

1. **ADK Agent** (`agent.py`)
   ```python
   from google.adk.agents import Agent
   
   root_agent = Agent(
       name="outline",
       model="gemini-2.0-flash-exp",
       description="Generates structured slide outlines",
       instruction="..."  # Full prompt template
   )
   ```

2. **A2A Executor** (`agent_executor.py`)
   ```python
   from a2a.server.agent_execution import AgentExecutor
   from google.adk import Runner
   
   class OutlineAgentExecutor(AgentExecutor):
       def __init__(self, runner: Runner, card: AgentCard):
           self.runner = runner
           self._card = card
   ```

3. **A2A Server** (`a2a_server.py`)
   - Handles A2A protocol communication
   - Manages agent lifecycle
   - Provides health endpoints

## File Structure

```
outline/
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
   - Defines outline generation logic via prompts
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
    name="outline",
    model="gemini-2.0-flash-exp",
    description="Generates structured slide outlines from clarified goals",
    instruction="""You are an expert presentation outliner...
    
    Input Format:
    - clarifiedContent: Presentation goals
    - constraints: Optional limits
    
    Output Format:
    {
        "outline": ["Title 1", "Title 2", ...]
    }
    """
)
```

### A2A Executor Pattern
```python
class OutlineAgentExecutor(AgentExecutor):
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
- Sessions maintain context across requests
- ArangoClient provides custom session storage if needed
- Session reuse for related outline generations

## Testing Requirements

### Unit Tests
```python
async def test_outline_generation():
    """Test outline generation with ADK runner."""
    runner = Runner(agent=root_agent)
    session = await runner.create_session()
    
    message = types.Content(
        parts=[types.Part(text=json.dumps({
            "clarifiedContent": "Create a 30-minute technical presentation on AI safety for engineers",
            "constraints": {"max_slides": 10}
        }))]
    )
    
    response = await runner.run(session, message)
    result = json.loads(response.text)
    assert "outline" in result
    assert 6 <= len(result["outline"]) <= 12
    assert all(isinstance(title, str) for title in result["outline"])
```

### Integration Tests
- A2A protocol compliance
- Pipeline integration with clarifier (upstream) and slide_writer (downstream)
- Constraint validation and enforcement
- Error handling for invalid input

### Performance Benchmarks
- **Response Time**: < 2 seconds via ADK
- **Token Usage**: ~500-1000 tokens per outline
- **Concurrent Sessions**: Handled by ADK Runner
- **Quality Metrics**: Logical flow, title clarity

## Common Modifications

### Updating the Prompt
**Location**: `agent.py` - `instruction` parameter
```python
root_agent = Agent(
    name="outline",
    model="gemini-2.0-flash-exp",
    instruction="Updated outlining instructions..."
)
```

### Adjusting Slide Count Range
Modify the instruction to change the default 6-12 slide range:
```python
instruction="""...
3. Generate 8-15 concise, action-oriented slide titles.
..."""
```

### Changing the Model
```python
root_agent = Agent(
    name="outline",
    model="gemini-2.0-flash-thinking-exp",  # Or other model
    ...
)
```

### Adding Validation
Implement additional validation in the executor:
```python
def validate_outline(outline):
    if not (6 <= len(outline) <= 12):
        raise ValueError("Outline must have 6-12 slides")
    for title in outline:
        if len(title.split()) > 8:
            raise ValueError("Titles should be 4-8 words")
```

## Agent-Specific Warnings

### ⚠️ What Breaks This Agent

1. **Invalid JSON Output**
   - Symptom: Downstream agents fail to parse outline
   - Cause: Model deviates from JSON format
   - Fix: Strengthen JSON instructions, add validation

2. **Poor Title Quality**
   - Symptom: Vague or overly long titles
   - Cause: Insufficient prompt guidance
   - Fix: Add examples of good vs bad titles

3. **Constraint Violations**
   - Symptom: Too many/few slides, ignoring limits
   - Cause: Model not respecting constraints
   - Fix: Emphasize constraints in prompt

### Critical Dependencies
- **Clarifier Agent**: Must provide clear, structured goals
- **Google ADK**: Core agent framework
- **A2A Protocol**: Agent communication layer
- **Gemini API**: LLM backend (via ADK)

### Performance Considerations
- Simple task, typically completes quickly
- Token usage is predictable and low
- Can handle multiple outline requests concurrently
- Caching possible for identical requests

## Pipeline Integration

### Upstream Dependencies
```
Clarifier Agent → (clarifiedContent) → Outline Agent
```

### Downstream Flow
```
Outline Agent → (outline array) → Slide Writer Agent
```

### Data Flow
1. Receives clarified goals from Clarifier
2. Generates structured outline
3. Passes outline array to Slide Writer
4. Each title becomes a slide to be expanded

### A2A Protocol Details
- Registered as "outline" agent
- Receives tasks with clarified content
- Returns outline array via task updater
- Supports streaming for real-time updates

## Deployment Notes

### Running Standalone
```bash
# With A2A server
python -m agents.outline.a2a_server

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
CMD ["python", "-m", "agents.outline.a2a_server"]
```

### Monitoring
- Track outline generation success rate
- Monitor average slide count
- Measure title quality metrics
- Token usage per outline

## Troubleshooting

### Common Issues

1. **Empty or Missing Outline**
   - Check input format matches expected schema
   - Verify clarifiedContent is not empty
   - Review model response for errors

2. **Inconsistent Slide Count**
   - Ensure constraints are properly formatted
   - Check if model is respecting limits
   - Consider adding validation layer

3. **Poor Logical Flow**
   - Review clarifiedContent quality
   - Enhance prompt with flow examples
   - Consider adding structure templates

4. **Title Length Issues**
   - Add word count validation
   - Provide more title examples
   - Emphasize brevity in prompt

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Quality Guidelines

### Good Outline Characteristics
- **Logical Flow**: Clear progression of ideas
- **Balanced Structure**: Even distribution of content
- **Action-Oriented**: Titles suggest content/purpose
- **Appropriate Scope**: Matches time constraints

### Title Best Practices
- 4-8 words per title
- Specific, not generic
- Consistent formatting
- Clear value proposition

### Common Patterns
1. **Standard Business**: Intro → Problem → Solution → Benefits → Implementation → Conclusion
2. **Technical**: Overview → Architecture → Deep Dive → Demo → Best Practices → Q&A
3. **Educational**: Objectives → Background → Concepts → Examples → Practice → Summary

## Migration Notes

This agent has been migrated from custom base classes to ADK/A2A:
- Previous: Inherited from `BaseAgent` and `BaseAgentExecutor`
- Current: Uses ADK `Agent` and A2A `AgentExecutor`
- Benefits: Simplified implementation, better error handling, automatic telemetry

## Future Enhancements

Potential improvements to consider:
- Template library for common presentation types
- Dynamic slide count based on content complexity
- Multi-language outline support
- Integration with design themes
- Audience-specific outline adaptation