# CLAUDE.md - Design Agent (ADK/A2A Implementation)

## Agent Purpose & Responsibility

**Single Responsibility**: Creates visual design specifications and layout recommendations for presentation slides, including backgrounds, patterns, and color schemes.

The Design agent transforms slide content into visually appealing presentations with professional aesthetics.

### Core Function
- Proposes background visuals for slides
- Generates CSS/SVG code for simple patterns
- Creates descriptive prompts for complex visuals
- Optimizes designs for text legibility
- Ensures professional appearance

### Input/Output Contracts

**Input** (JSON):
```json
{
    "slide": {
        "title": "Slide Title",
        "content": ["bullet 1", "bullet 2"]
    },
    "theme": "brand",
    "pattern": "gradient"
}
```

**Output** (JSON):
```json
{
    "type": "code",
    "code": {
        "css": "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);",
        "svg": "<svg>...</svg>"
    },
    "prompt": null
}
```
OR
```json
{
    "type": "prompt",
    "code": null,
    "prompt": "Abstract geometric pattern with..."
}
```

## ADK/A2A Architecture

### Framework Components

1. **ADK Agent** (`agent.py`)
   ```python
   from google.adk.agents import Agent
   
   root_agent = Agent(
       name="design",
       model="gemini-2.0-flash",
       description="Creates visual design specifications",
       instruction="..."
   )
   ```

2. **A2A Executor** (`agent_executor.py`)
   ```python
   from a2a.server.agent_execution import AgentExecutor
   
   class DesignAgentExecutor(AgentExecutor):
       def __init__(self, runner: Runner, card: AgentCard):
           self.runner = runner
           self._card = card
   ```

## File Structure

```
design/
├── __init__.py
├── agent.py                 # ADK Agent definition
├── agent_executor.py        # A2A AgentExecutor
├── a2a_server.py           # A2A protocol server
├── ArangoClient.py         # Database session management
├── Dockerfile
└── CLAUDE.md
```

## Implementation Details

### Theme Options
- **Brand**: Company colors and identity
- **Dark**: Dark mode with high contrast
- **Light**: Clean, minimal aesthetic
- **Vibrant**: Bold, energetic colors
- **Professional**: Conservative business style

### Pattern Types
- **Gradient**: Smooth color transitions
- **Grid**: Geometric grid patterns
- **Abstract**: Non-representational designs
- **Minimal**: Simple, clean backgrounds
- **Texture**: Subtle textured effects

### Design Principles
1. **Legibility**: Ensure text remains readable
2. **Consistency**: Maintain theme throughout
3. **Balance**: Visual weight distribution
4. **Hierarchy**: Guide viewer attention
5. **Accessibility**: Consider color contrast

## Testing Requirements

### Unit Tests
```python
async def test_design_generation():
    """Test design specification generation."""
    runner = Runner(agent=root_agent)
    session = await runner.create_session()
    
    message = types.Content(
        parts=[types.Part(text=json.dumps({
            "slide": {"title": "Introduction", "content": ["Point 1"]},
            "theme": "brand",
            "pattern": "gradient"
        }))]
    )
    
    response = await runner.run(session, message)
    result = json.loads(response.text)
    assert result["type"] in ["code", "prompt"]
```

## Pipeline Integration

### Upstream Dependencies
```
Slide Writer → (slide content) → Design
Image Prompts → Design
```

### Downstream Flow
```
Design → (visual specs) → Frontend Rendering
Design → (image prompts) → Image Generation
```

## Migration Notes

This agent has been migrated from custom base classes to ADK/A2A:
- Previous: Inherited from `BaseAgent` and `BaseAgentExecutor`
- Current: Uses ADK `Agent` and A2A `AgentExecutor`
- Benefits: Better design consistency, improved CSS generation