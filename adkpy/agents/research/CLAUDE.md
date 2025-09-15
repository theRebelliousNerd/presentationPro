# CLAUDE.md - Research Agent (ADK/A2A Implementation)

## Agent Purpose & Responsibility

**Single Responsibility**: Gathers background information, statistics, and supporting data to enrich presentation content with authoritative sources.

The Research agent provides data-driven insights and evidence to support presentation claims.

### Core Function
- Finds relevant statistics and data points
- Identifies industry trends and insights
- Gathers case studies and examples
- Locates authoritative sources and citations
- Provides context and background information

### Input/Output Contracts

**Input** (JSON):
```json
{
    "query": "AI adoption rates in healthcare 2024"
}
```

**Output** (JSON):
```json
{
    "findings": [
        {
            "fact": "78% of healthcare providers use AI tools",
            "source": "Healthcare AI Report 2024",
            "relevance": "Demonstrates widespread adoption"
        }
    ],
    "trends": ["Increasing use of predictive analytics"],
    "examples": ["Mayo Clinic's AI diagnostic system"],
    "sources": ["https://example.com/report.pdf"]
}
```

## ADK/A2A Architecture

### Framework Components

1. **ADK Agent** (`agent.py`)
   ```python
   from google.adk.agents import Agent
   
   root_agent = Agent(
       name="research",
       model="gemini-2.0-flash",
       description="Gathers background information and data",
       instruction="..."
   )
   ```

2. **A2A Executor** (`agent_executor.py`)
   ```python
   from a2a.server.agent_execution import AgentExecutor
   
   class ResearchAgentExecutor(AgentExecutor):
       def __init__(self, runner: Runner, card: AgentCard):
           self.runner = runner
           self._card = card
   ```

## File Structure

```
research/
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

### Research Categories
1. **Statistics**: Quantitative data and metrics
2. **Trends**: Industry directions and patterns
3. **Case Studies**: Real-world examples
4. **Best Practices**: Proven methodologies
5. **Background**: Historical context

### Data Quality Criteria
- **Recency**: Prefer recent sources (< 2 years)
- **Authority**: Credible sources only
- **Relevance**: Direct connection to query
- **Accuracy**: Verified information
- **Completeness**: Comprehensive coverage

## Testing Requirements

### Unit Tests
```python
async def test_research_gathering():
    """Test research data gathering."""
    runner = Runner(agent=root_agent)
    session = await runner.create_session()
    
    message = types.Content(
        parts=[types.Part(text=json.dumps({
            "query": "cloud computing trends 2024"
        }))]
    )
    
    response = await runner.run(session, message)
    result = json.loads(response.text)
    assert "findings" in result or "rules" in result
```

## Pipeline Integration

### Upstream Dependencies
```
Clarifier → (topics to research) → Research
Outline → (slide topics) → Research
```

### Downstream Flow
```
Research → (data/citations) → Slide Writer
Research → (sources) → Script Writer
Research → (facts) → Critic (validation)
```

## Tools Integration

The Research agent may integrate with:
- Web search APIs
- Academic databases
- Industry reports
- ArangoDB for cached research
- RAG systems for document retrieval

## Migration Notes

This agent has been migrated from custom base classes to ADK/A2A:
- Previous: Inherited from `BaseAgent` and `BaseAgentExecutor`
- Current: Uses ADK `Agent` and A2A `AgentExecutor`
- Benefits: Better source tracking, improved data quality