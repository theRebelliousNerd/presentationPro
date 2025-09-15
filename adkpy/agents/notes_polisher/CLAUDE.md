# CLAUDE.md - Notes Polisher Agent (ADK/A2A Implementation)

## Agent Purpose & Responsibility

**Single Responsibility**: Polishes and enhances speaker notes for smooth, confident presentation delivery with specific tone targeting.

The Notes Polisher agent refines speaker notes to match the desired presentation tone and improve delivery flow.

### Core Function
- Enhances speaker notes for smooth delivery
- Rephrases notes to match target tone (professional, engaging, etc.)
- Improves clarity and flow while maintaining core message
- Optimizes for presenter confidence and impact

### Input/Output Contracts

**Input** (JSON):
```json
{
    "speakerNotes": "Original speaker notes to be polished",
    "tone": "professional"
}
```

**Output** (JSON):
```json
{
    "rephrasedSpeakerNotes": "Enhanced notes with improved flow and tone..."
}
```

## ADK/A2A Architecture

### Framework Components

1. **ADK Agent** (`agent.py`)
   ```python
   from google.adk.agents import Agent
   
   root_agent = Agent(
       name="notes_polisher",
       model="gemini-2.0-flash",
       description="Polishes speaker notes for presentation delivery",
       instruction="..."
   )
   ```

2. **A2A Executor** (`agent_executor.py`)
   ```python
   from a2a.server.agent_execution import AgentExecutor
   
   class NotesPolisherAgentExecutor(AgentExecutor):
       def __init__(self, runner: Runner, card: AgentCard):
           self.runner = runner
           self._card = card
   ```

## File Structure

```
notes_polisher/
├── __init__.py
├── agent.py                 # ADK Agent definition
├── agent_executor.py        # A2A AgentExecutor
├── a2a_server.py           # A2A protocol server
├── ArangoClient.py         # Database session management
├── requirements.txt
├── Dockerfile
└── CLAUDE.md
```

## Implementation Details

### Tone Options
- **Professional**: Formal, authoritative, structured
- **Engaging**: Conversational, enthusiastic, relatable
- **Technical**: Precise, detailed, expert-oriented
- **Casual**: Friendly, approachable, simple
- **Inspirational**: Motivating, visionary, passionate

### Enhancement Strategies
1. **Flow Improvement**: Add transitions between points
2. **Clarity Enhancement**: Simplify complex explanations
3. **Engagement Tactics**: Add rhetorical questions, examples
4. **Confidence Building**: Remove hedging language
5. **Time Management**: Ensure appropriate pacing cues

## Testing Requirements

### Unit Tests
```python
async def test_notes_polishing():
    """Test speaker notes enhancement."""
    runner = Runner(agent=root_agent)
    session = await runner.create_session()
    
    message = types.Content(
        parts=[types.Part(text=json.dumps({
            "speakerNotes": "Talk about the benefits. Mention cost savings.",
            "tone": "professional"
        }))]
    )
    
    response = await runner.run(session, message)
    result = json.loads(response.text)
    assert "rephrasedSpeakerNotes" in result
    assert len(result["rephrasedSpeakerNotes"]) > 0
```

## Pipeline Integration

### Upstream Dependencies
```
Slide Writer → (speaker notes) → Notes Polisher
Critic → (refined notes) → Notes Polisher
```

### Downstream Flow
```
Notes Polisher → (polished notes) → Final Presentation
```

## Migration Notes

This agent has been migrated from custom base classes to ADK/A2A:
- Previous: Inherited from `BaseAgent` and `BaseAgentExecutor`
- Current: Uses ADK `Agent` and A2A `AgentExecutor`
- Benefits: Consistent tone application, better language flow