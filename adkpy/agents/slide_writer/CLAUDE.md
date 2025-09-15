# CLAUDE.md - Slide Writer Agent (ADK/A2A Implementation)

## Agent Purpose & Responsibility

**Single Responsibility**: Generates comprehensive content for individual presentation slides, including bullet points, speaker notes, and image prompts.

The Slide Writer agent is the **third agent** in the presentation pipeline, transforming outline titles into fully-developed slide content.

### Core Function
- Expands slide titles into complete slide content
- Creates 2-4 concise bullet points (≤12 words each)
- Writes detailed speaker notes with talking points
- Generates descriptive image prompts for visual content
- Grounds content in provided assets when available

### Input/Output Contracts

**Input** (JSON):
```json
{
    "title": "The slide title to expand",
    "assets": ["Optional asset content for grounding"],
    "constraints": {
        "tone": "professional",
        "audience": "technical"
    }
}
```

**Output** (JSON):
```json
{
    "title": "The slide title",
    "content": [
        "First bullet point",
        "Second bullet point",
        "Third bullet point"
    ],
    "speakerNotes": "Detailed talking points for the presenter...",
    "imagePrompt": "A descriptive prompt for generating slide visuals..."
}
```

## ADK/A2A Architecture

### Framework Components
This agent uses Google's ADK (Agent Development Kit) and A2A (Agent-to-Agent) protocol:

1. **ADK Agent** (`agent.py`)
   ```python
   from google.adk.agents import Agent
   
   root_agent = Agent(
       name="slide_writer",
       model="gemini-2.0-flash",
       description="Generates comprehensive slide content",
       instruction="..."  # Full prompt template
   )
   ```

2. **A2A Executor** (`agent_executor.py`)
   ```python
   from a2a.server.agent_execution import AgentExecutor
   from google.adk import Runner
   
   class SlideWriterAgentExecutor(AgentExecutor):
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
slide_writer/
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
   - Defines slide content generation logic
   - JSON response format specification

2. **`agent_executor.py`**
   - Inherits from A2A's `AgentExecutor`
   - Implements `_process_request()` for task handling
   - Manages sessions via ADK's Runner
   - Handles batch processing of multiple slides

3. **`a2a_server.py`** (if running standalone)
   - A2A server setup and configuration
   - Agent card registration
   - Protocol endpoint handlers

## Implementation Details

### ADK Agent Definition
```python
root_agent = Agent(
    name="slide_writer",
    model="gemini-2.0-flash",
    description="Generates comprehensive slide content",
    instruction="""You are a Slide Writer agent...
    
    1. Generate complete content for slides
    2. Create 2-4 concise bullet points
    3. Write detailed speaker notes
    4. Generate image prompts
    
    Input Format:
    - title: Slide title
    - assets: Optional content
    - constraints: Optional limits
    
    Output Format:
    {
        "title": "...",
        "content": ["bullet 1", ...],
        "speakerNotes": "...",
        "imagePrompt": "..."
    }
    """
)
```

### A2A Executor Pattern
```python
class SlideWriterAgentExecutor(AgentExecutor):
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

### Batch Processing
The agent can process multiple slides in sequence:
```python
for slide_title in outline:
    input_data = {
        "title": slide_title,
        "assets": relevant_assets,
        "constraints": presentation_constraints
    }
    # Process each slide
```

## Testing Requirements

### Unit Tests
```python
async def test_slide_content_generation():
    """Test slide content generation with ADK runner."""
    runner = Runner(agent=root_agent)
    session = await runner.create_session()
    
    message = types.Content(
        parts=[types.Part(text=json.dumps({
            "title": "Introduction to Machine Learning",
            "assets": ["ML is a subset of AI..."],
            "constraints": {"audience": "beginners"}
        }))]
    )
    
    response = await runner.run(session, message)
    result = json.loads(response.text)
    assert "content" in result
    assert 2 <= len(result["content"]) <= 4
    assert "speakerNotes" in result
    assert "imagePrompt" in result
```

### Integration Tests
- Pipeline integration with outline (upstream) and critic (downstream)
- Asset incorporation validation
- Constraint adherence testing
- Batch processing of multiple slides

### Performance Benchmarks
- **Response Time**: < 4 seconds per slide
- **Token Usage**: ~800-1500 tokens per slide
- **Batch Processing**: 10-15 slides per minute
- **Quality Metrics**: Bullet conciseness, note completeness

## Common Modifications

### Updating the Prompt
**Location**: `agent.py` - `instruction` parameter
```python
root_agent = Agent(
    name="slide_writer",
    model="gemini-2.0-flash",
    instruction="Updated slide writing instructions..."
)
```

### Adjusting Bullet Point Count
Modify the instruction to change bullet point limits:
```python
instruction="""...
2. Create 3-5 concise bullet points (15 words or fewer each).
..."""
```

### Changing the Model
```python
root_agent = Agent(
    name="slide_writer",
    model="gemini-2.0-flash-exp",  # Or other model
    ...
)
```

### Enhancing Image Prompts
Add more detailed image generation guidance:
```python
instruction="""...
4. Generate a descriptive image prompt that includes:
   - Visual style (photo, illustration, diagram)
   - Key elements to include
   - Color scheme and mood
..."""
```

## Agent-Specific Warnings

### ⚠️ What Breaks This Agent

1. **Overly Long Bullet Points**
   - Symptom: Bullets exceed display limits
   - Cause: Model ignoring word count constraint
   - Fix: Strengthen brevity instructions, add validation

2. **Missing Content Fields**
   - Symptom: Incomplete slide data
   - Cause: JSON format deviation
   - Fix: Validate output schema, provide examples

3. **Poor Asset Integration**
   - Symptom: Generated content ignores provided assets
   - Cause: Weak asset incorporation instructions
   - Fix: Emphasize asset usage in prompt

4. **Generic Speaker Notes**
   - Symptom: Notes lack depth or specificity
   - Cause: Insufficient guidance on note quality
   - Fix: Provide examples of good speaker notes

### Critical Dependencies
- **Outline Agent**: Provides slide titles
- **Asset Processing**: Optional but enhances quality
- **Google ADK**: Core agent framework
- **Gemini API**: LLM backend (via ADK)

### Performance Considerations
- Processes slides individually for consistency
- Can batch process for efficiency
- Token usage scales with content complexity
- Image prompt generation adds minimal overhead

## Pipeline Integration

### Upstream Dependencies
```
Outline Agent → (slide titles) → Slide Writer
Assets/Files → (optional grounding) → Slide Writer
```

### Downstream Flow
```
Slide Writer → (complete slides) → Critic Agent
Slide Writer → (complete slides) → Notes Polisher
Slide Writer → (image prompts) → Design Agent
```

### Data Flow
1. Receives slide titles from Outline
2. Optionally incorporates asset content
3. Generates complete slide content
4. Passes to multiple downstream agents for refinement

### A2A Protocol Details
- Registered as "slide_writer" agent
- Processes individual slide requests
- Returns complete slide objects
- Supports streaming for progress updates

## Deployment Notes

### Running Standalone
```bash
# With A2A server
python -m agents.slide_writer.a2a_server

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
CMD ["python", "-m", "agents.slide_writer.a2a_server"]
```

### Monitoring
- Track slide generation success rate
- Monitor bullet point word counts
- Measure speaker notes quality
- Token usage per slide

## Quality Guidelines

### Bullet Points
- **Concise**: 12 words or fewer
- **Clear**: Single concept per bullet
- **Parallel**: Consistent structure
- **Action-Oriented**: Start with verbs when possible

### Speaker Notes
- **Comprehensive**: Cover all bullet points
- **Conversational**: Natural speaking flow
- **Timed**: Appropriate for slide duration
- **Structured**: Clear transitions

### Image Prompts
- **Specific**: Clear visual description
- **Relevant**: Matches slide content
- **Feasible**: Can be generated/found
- **Professional**: Appropriate style

## Troubleshooting

### Common Issues

1. **Incomplete Slide Content**
   - Verify input format is correct
   - Check for JSON parsing errors
   - Review model response completeness

2. **Word Count Violations**
   - Add post-processing validation
   - Strengthen prompt constraints
   - Consider truncation logic

3. **Poor Asset Integration**
   - Ensure assets are properly formatted
   - Check asset relevance to slide
   - Review incorporation instructions

4. **Generic Content**
   - Provide more context in input
   - Use constraints effectively
   - Consider domain-specific prompts

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
- Benefits: Better streaming support, automatic retries, simplified code

## Future Enhancements

Potential improvements to consider:
- Template library for common slide types
- Multi-language content generation
- Dynamic bullet count based on complexity
- Integration with citation management
- Real-time collaboration features
- Smart asset selection algorithms