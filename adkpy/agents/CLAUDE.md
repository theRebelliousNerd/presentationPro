# CLAUDE.md - Multi-Agent Presentation System (ADK/A2A Architecture)

## System Overview

This directory contains a sophisticated multi-agent system for AI-powered presentation creation, built on Google's Agent Development Kit (ADK) and Agent-to-Agent (A2A) protocol. The system orchestrates specialized agents to transform user ideas into complete, professional presentations.

## Architecture

### Technology Stack
- **Framework**: Google ADK (Agent Development Kit)
- **Protocol**: A2A (Agent-to-Agent) communication
- **Language**: Python 3.11+
- **LLM**: Google Gemini models (2.0-flash, 2.0-flash-exp)
- **Database**: ArangoDB for session management and RAG
- **Orchestration**: Custom orchestrator with parallel execution

### System Design
```
User Input → Orchestrator → Clarifier → Outline → Slide Writer → Critic
                    ↓                                    ↓          ↓
                Research                          Notes Polisher  Design
                                                        ↓          ↓
                                                  Script Writer → Output
```

## Agent Directory Structure

```
agents/
├── base/                    # Legacy/shared utilities (being deprecated)
│   ├── a2a_base.py         # A2A protocol utilities
│   ├── agent_base.py       # DEPRECATED - Legacy base classes
│   ├── agent_executor_base.py # DEPRECATED - Legacy executor
│   ├── remote_connection.py # Connection utilities
│   └── session_manager.py  # Session management
│
├── orchestrate/            # Central orchestration hub
│   ├── agent.py           # HostAgent orchestrator
│   ├── agent_executor.py  # Workflow execution
│   └── remote_agent_connection.py # A2A connections
│
├── clarifier/              # Goal refinement agent
│   ├── agent.py           # ADK Agent definition
│   ├── agent_executor.py  # A2A AgentExecutor
│   └── a2a_server.py      # Standalone server
│
├── outline/                # Structure generation agent
│   ├── agent.py           # Creates presentation outline
│   └── agent_executor.py  # Outline task execution
│
├── slide_writer/           # Content creation agent
│   ├── agent.py           # Generates slide content
│   └── agent_executor.py  # Batch slide processing
│
├── critic/                 # Quality assurance agent
│   ├── agent.py           # Enforces standards
│   └── agent_executor.py  # Review and validation
│
├── notes_polisher/         # Speaker notes enhancement
│   ├── agent.py           # Polishes delivery notes
│   └── agent_executor.py  # Note processing
│
├── design/                 # Visual design agent
│   ├── agent.py           # Creates visual specs
│   └── agent_executor.py  # Design generation
│
├── script_writer/          # Narrative creation agent
│   ├── agent.py           # Writes full scripts
│   └── agent_executor.py  # Script compilation
│
└── research/               # Data gathering agent
    ├── agent.py           # Finds supporting data
    └── agent_executor.py  # Research execution
```

## Agent Responsibilities

### Core Pipeline Agents

1. **Clarifier** (`clarifier/`)
   - First agent in pipeline
   - Refines vague requests through Q&A
   - Outputs structured goals

2. **Outline** (`outline/`)
   - Creates logical presentation structure
   - Generates 6-12 slide titles
   - Ensures proper flow

3. **Slide Writer** (`slide_writer/`)
   - Expands titles into full content
   - Creates bullets, notes, image prompts
   - Processes slides in batch

4. **Critic** (`critic/`)
   - Quality gate enforcement
   - Validates structure and citations
   - Ensures standards compliance

### Enhancement Agents

5. **Notes Polisher** (`notes_polisher/`)
   - Enhances speaker notes
   - Adjusts tone and flow
   - Optimizes for delivery

6. **Design** (`design/`)
   - Creates visual specifications
   - Generates CSS/SVG or prompts
   - Ensures aesthetic consistency

7. **Script Writer** (`script_writer/`)
   - Creates full presentation narrative
   - Adds transitions and citations
   - Generates bibliography

8. **Research** (`research/`)
   - Gathers supporting data
   - Finds statistics and examples
   - Provides authoritative sources

### System Agent

9. **Orchestrate** (`orchestrate/`)
   - Central coordination hub
   - Manages agent communication
   - Handles workflow execution
   - Tracks progress and errors

## ADK/A2A Implementation

### Agent Pattern
Each agent follows this structure:
```python
# agent.py - ADK Agent definition
from google.adk.agents import Agent

root_agent = Agent(
    name="agent_name",
    model="gemini-2.0-flash-exp",
    description="Agent purpose",
    instruction="Detailed prompt..."
)

# agent_executor.py - A2A Executor
from a2a.server.agent_execution import AgentExecutor

class AgentNameExecutor(AgentExecutor):
    def __init__(self, runner: Runner, card: AgentCard):
        self.runner = runner
        self._card = card
```

### Communication Flow
1. Orchestrator sends task via A2A protocol
2. Agent executor receives and processes
3. ADK Runner manages LLM interaction
4. Results returned through task updater
5. Orchestrator aggregates responses

## Configuration

### Environment Setup
```bash
# Required
GOOGLE_GENAI_API_KEY=your_key_here

# Optional
ARANGO_URL=http://localhost:8529
BING_SEARCH_API_KEY=your_key_here

# Agent URLs (for orchestrator)
CLARIFIER_URL=http://localhost:10001
OUTLINE_URL=http://localhost:10002
# ... etc
```

### Model Configuration
Agents use different Gemini models based on task complexity:
- **gemini-2.0-flash**: Fast, efficient for simple tasks
- **gemini-2.0-flash-exp**: Experimental, better reasoning
- **gemini-2.0-flash-thinking-exp**: Advanced reasoning (when needed)

## Development Guidelines

### Adding New Agents
1. Create new directory under `agents/`
2. Implement `agent.py` with ADK Agent
3. Implement `agent_executor.py` with A2A AgentExecutor
4. Add `a2a_server.py` if standalone deployment needed
5. Create `CLAUDE.md` documentation
6. Register with orchestrator

### Agent Requirements
- Single responsibility principle
- Clear input/output contracts (JSON)
- Proper error handling
- Comprehensive logging
- Unit and integration tests
- Performance benchmarks

### Code Standards
```python
# Standard imports
from google.adk.agents import Agent
from a2a.server.agent_execution import AgentExecutor
from a2a.types import AgentCard, TaskState

# Consistent naming
class {AgentName}AgentExecutor(AgentExecutor):
    pass

# Proper async handling
async def _process_request(...):
    pass
```

## Testing

### Unit Tests
Each agent should have tests for:
- Input validation
- Core functionality
- Output formatting
- Error scenarios

### Integration Tests
Test agent interactions:
- Pipeline flow
- Parallel execution
- Error propagation
- Recovery mechanisms

### Performance Tests
Benchmark critical metrics:
- Response time
- Token usage
- Memory consumption
- Concurrent handling

## Deployment

### Local Development
```bash
# Run individual agent
python -m agents.clarifier.a2a_server

# Run orchestrator with all agents
python -m agents.orchestrate.agent
```

### Docker Deployment
```bash
# Build all agents
docker-compose build

# Run specific agents
docker-compose up orchestrator clarifier outline

# Run complete system
docker-compose up
```

### Production Considerations
- Use environment-specific configs
- Implement health checks
- Set up monitoring/alerting
- Configure rate limiting
- Enable distributed tracing

## Monitoring & Debugging

### Key Metrics
- Agent response times
- Token usage per agent
- Error rates
- Retry counts
- Session durations

### Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Agent-specific loggers
logger = logging.getLogger(__name__)
```

### Common Issues
1. **Agent timeout**: Increase timeout settings
2. **Token limits**: Implement content chunking
3. **Connection failures**: Check A2A server status
4. **Poor quality**: Review agent prompts
5. **Slow performance**: Consider parallel execution

## Migration Status

### Completed
- ✅ All agents migrated to ADK/A2A
- ✅ Orchestrator implements A2A protocol
- ✅ Session management via ADK
- ✅ Parallel agent execution

### In Progress
- 🔄 Deprecating base classes
- 🔄 Optimizing agent prompts
- 🔄 Performance tuning

### Planned
- 📋 Dynamic agent discovery
- 📋 Advanced caching strategies
- 📋 Multi-tenant support
- 📋 Real-time progress streaming

## Contributing

### Development Workflow
1. Create feature branch
2. Implement changes with tests
3. Update relevant CLAUDE.md files
4. Ensure all tests pass
5. Submit PR with clear description

### Code Review Checklist
- [ ] Follows ADK/A2A patterns
- [ ] Includes proper error handling
- [ ] Has comprehensive tests
- [ ] Documentation updated
- [ ] Performance impact assessed

## Resources

### Documentation
- [Google ADK Docs](https://developers.google.com/agent-development-kit)
- [A2A Protocol Spec](https://github.com/google/a2a-protocol)
- Individual agent CLAUDE.md files

### Support
- GitHub Issues for bug reports
- Discussions for feature requests
- Wiki for extended documentation

## License

[Specify your license here]

---

*Last Updated: [Current Date]*
*System Version: ADK/A2A Architecture v2.0*