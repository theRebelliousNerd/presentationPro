# CLAUDE.md - Critic Agent (ADK/A2A Implementation)

## Agent Purpose & Responsibility

**Single Responsibility**: Quality assurance agent that enforces presentation standards, validates content structure, and adds asset citations.

The Critic agent acts as a quality gate in the presentation pipeline, ensuring all slides meet strict standards before finalization.

### Core Function
- Enforces quality standards on slide drafts
- Ensures titles are sharp and specific (3-6 words)
- Validates bullet points (2-4 points, max 12 words each)
- Adds asset citations using [ref: filename] format
- Corrects speaker notes for conciseness and relevance
- Aligns image prompts with corrected content

### Input/Output Contracts

**Input** (JSON):
```json
{
    "slideDraft": {
        "title": "Draft slide title",
        "content": ["bullet 1", "bullet 2"],
        "speakerNotes": "Draft notes",
        "imagePrompt": "Draft prompt"
    },
    "assets": [{"filename": "doc.pdf", "content": "..."}]
}
```

**Output** (JSON):
```json
{
    "title": "Refined Title",
    "content": [
        "Improved bullet [ref: doc.pdf]",
        "Second refined bullet"
    ],
    "speakerNotes": "Corrected and concise speaker notes...",
    "imagePrompt": "Aligned image generation prompt..."
}
```

## ADK/A2A Architecture

### Framework Components

1. **ADK Agent** (`agent.py`)
   ```python
   from google.adk.agents import Agent
   
   root_agent = Agent(
       name="critic",
       model="gemini-2.0-flash",
       description="Quality assurance agent enforcing standards",
       instruction="..."
   )
   ```

2. **A2A Executor** (`agent_executor.py`)
   ```python
   from a2a.server.agent_execution import AgentExecutor
   
   class CriticAgentExecutor(AgentExecutor):
       def __init__(self, runner: Runner, card: AgentCard):
           self.runner = runner
           self._card = card
   ```

## File Structure

```
critic/
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

### Quality Enforcement Rules

1. **Title Standards**
   - 3-6 words maximum
   - Clear and specific
   - No generic phrases

2. **Bullet Point Standards**
   - 2-4 bullets per slide
   - Maximum 12 words each
   - Parallel structure
   - Action-oriented

3. **Citation Standards**
   - Format: [ref: filename]
   - Place after relevant facts
   - Verify source accuracy

4. **Speaker Notes Standards**
   - Concise but comprehensive
   - Natural speaking flow
   - 100-200 words typical

## Testing Requirements

### Unit Tests
```python
async def test_critic_quality_enforcement():
    """Test quality standards enforcement."""
    runner = Runner(agent=root_agent)
    session = await runner.create_session()
    
    message = types.Content(
        parts=[types.Part(text=json.dumps({
            "slideDraft": {
                "title": "This is a very long title that needs to be shortened",
                "content": ["A bullet point that is way too long and needs refinement"],
                "speakerNotes": "Notes",
                "imagePrompt": "image"
            }
        }))]
    )
    
    response = await runner.run(session, message)
    result = json.loads(response.text)
    assert len(result["title"].split()) <= 6
    assert all(len(b.split()) <= 12 for b in result["content"])
```

## Common Modifications

### Adjusting Quality Standards
Modify the instruction to change enforcement rules:
```python
instruction="""...
2. Ensure titles are sharp and specific (4-8 words).
3. Validate bullet points (3-5 points, max 15 words each).
..."""
```

## Pipeline Integration

### Upstream Dependencies
```
Slide Writer → (draft slides) → Critic
```

### Downstream Flow
```
Critic → (refined slides) → Final Presentation
```

## Migration Notes

This agent has been migrated from custom base classes to ADK/A2A:
- Previous: Inherited from `BaseAgent` and `BaseAgentExecutor`
- Current: Uses ADK `Agent` and A2A `AgentExecutor`
- Benefits: Consistent quality enforcement, better error handling