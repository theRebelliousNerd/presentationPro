# CLAUDE.md - Script Writer Agent (ADK/A2A Implementation)

## Agent Purpose & Responsibility

**Single Responsibility**: Transforms complete slide decks into cohesive presenter-ready scripts with smooth transitions and proper citations.

The Script Writer agent creates comprehensive presentation narratives that guide presenters through their entire talk.

### Core Function
- Transforms slide decks into cohesive scripts
- Creates smooth transitions between topics
- Integrates inline citations [ref: filename]
- Generates comprehensive bibliographies
- Ensures narrative flow and coherence

### Input/Output Contracts

**Input** (JSON):
```json
{
    "slides": [
        {
            "title": "Introduction",
            "content": ["Point 1", "Point 2"],
            "speakerNotes": "Welcome everyone..."
        }
    ],
    "assets": [
        {
            "name": "research.pdf",
            "url": "http://example.com/research.pdf"
        }
    ]
}
```

**Output** (JSON):
```json
{
    "script": "Good morning everyone. Today we'll explore... [ref: research.pdf]... Moving to our next topic..."
}
```

## ADK/A2A Architecture

### Framework Components

1. **ADK Agent** (`agent.py`)
   ```python
   from google.adk.agents import Agent
   
   root_agent = Agent(
       name="script_writer",
       model="gemini-2.0-flash",
       description="Writes complete presentation scripts",
       instruction="..."
   )
   ```

2. **A2A Executor** (`agent_executor.py`)
   ```python
   from a2a.server.agent_execution import AgentExecutor
   
   class ScriptWriterAgentExecutor(AgentExecutor):
       def __init__(self, runner: Runner, card: AgentCard):
           self.runner = runner
           self._card = card
   ```

## File Structure

```
script_writer/
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

### Script Components
1. **Opening**: Attention grabber, objectives
2. **Body**: Main content with transitions
3. **Transitions**: Smooth topic connections
4. **Citations**: Inline references [ref: source]
5. **Closing**: Summary, call to action
6. **Bibliography**: Complete source list

### Transition Patterns
- **Sequential**: "Moving on to...", "Next, we'll explore..."
- **Causal**: "As a result...", "This leads us to..."
- **Comparative**: "In contrast...", "Similarly..."
- **Temporal**: "Previously...", "Looking ahead..."

### Citation Format
- Inline: [ref: filename]
- Bibliography: Full source details
- URL preservation for references

## Testing Requirements

### Unit Tests
```python
async def test_script_generation():
    """Test script writing from slides."""
    runner = Runner(agent=root_agent)
    session = await runner.create_session()
    
    message = types.Content(
        parts=[types.Part(text=json.dumps({
            "slides": [
                {
                    "title": "Introduction",
                    "content": ["Key point"],
                    "speakerNotes": "Welcome"
                }
            ],
            "assets": []
        }))]
    )
    
    response = await runner.run(session, message)
    result = json.loads(response.text)
    assert "script" in result
    assert len(result["script"]) > 0
```

## Pipeline Integration

### Upstream Dependencies
```
Slide Writer → (complete slides) → Script Writer
Critic → (refined slides) → Script Writer
Assets → (citations) → Script Writer
```

### Downstream Flow
```
Script Writer → (full script) → Presenter View
Script Writer → (bibliography) → References Section
```

## Common Modifications

### Adjusting Script Style
Modify the instruction to change script tone:
```python
instruction="""...
2. Create smooth, conversational transitions...
3. Use a professional/casual/engaging tone...
..."""
```

### Citation Customization
Change citation format as needed:
```python
instruction="""...
3. Integrate citations using (Author, Year) format...
..."""
```

## Migration Notes

This agent has been migrated from custom base classes to ADK/A2A:
- Previous: Inherited from `BaseAgent` and `BaseAgentExecutor`
- Current: Uses ADK `Agent` and A2A `AgentExecutor`
- Benefits: Better narrative flow, consistent citation handling