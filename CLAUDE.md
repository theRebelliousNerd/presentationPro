# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Next-Gen Presentation Studio - An AI-powered presentation creation tool that guides users through a multi-step process to create presentations using Google's Agent Development Kit (ADK) and Agent-to-Agent (A2A) protocol with advanced workflow orchestration and Graph RAG integration.

## Development Commands

```bash
# Frontend Development (MUST use port 3000)
npm run dev                  # Next.js with Turbopack
npm run build               # Production build
npm run start               # Production server
npm run lint                # ESLint
npm run typecheck           # TypeScript checking

# Docker Development (Recommended)
docker compose up --build web       # Frontend only
docker compose up --build           # Full stack with all services
docker compose up --build web adkpy arangodb  # Full stack with ADK backend

# Backend Services
docker compose up -d adkpy          # Python ADK/A2A orchestrator (port 8089)
docker compose up -d arangodb       # Graph database (port 8530)
```

## Architecture Overview

### AI Backend System (ADK/A2A)

The app uses Google's Agent Development Kit (ADK) with Agent-to-Agent (A2A) protocol:

- **Architecture**: Python FastAPI backend with ADK agent wrappers
- **Multi-agent orchestration**: Each agent specializes in a specific task
- **Agents**: Clarifier, Outline, SlideWriter, Critic, NotesPolisher, Design, ScriptWriter, Research
- **Model Configuration**: Per-agent model selection via Settings panel
- **Backend**: Runs on port 8089 (exposed) / 8088 (internal Docker)

**Model Configuration Flow**:
1. User selects models in Settings → Saved to localStorage
2. Frontend sends model with each request (textModel, writerModel, criticModel)
3. Agent wrappers receive and use specified models
4. Model names normalized (strips "googleai/" prefix)

### Application Flow States

The app progresses through distinct states (`src/lib/types.ts`):
1. `initial` - User input (text, files, parameters)
2. `clarifying` - AI chat to refine goals (Context Meter tracks understanding)
3. `approving` - User reviews generated outline
4. `generating` - AI creates slide content
5. `editing` - User refines presentation
6. `error` - Error handling

### Core Architecture

**Frontend (Next.js 15.3.3)**
- `src/app/page.tsx` - Main orchestrator component
- `src/lib/orchestrator.ts` - ADK backend client
- `src/lib/actions.ts` - Server actions that route to ADK backend
- `src/hooks/use-presentation-state.ts` - State management with localStorage persistence
- `src/lib/agent-models.ts` - Model configuration for each agent

**ADK Backend (`adkpy/`)**
- `app/main.py` - FastAPI endpoints (`/v1/clarify`, `/v1/outline`, `/v1/slide`, etc.)
- `app/llm.py` - Gemini API wrapper (strips "googleai/" prefix from model names)
- `agents/wrappers.py` - Agent wrapper classes with model configuration support
- `agents/` - Individual microservice agent directories
- `tools/` - ArangoGraphRAG, WebSearch, Telemetry, AssetsIngest
- `a2a/` - Protocol definitions and policies

**Database**
- ArangoDB for Graph RAG (port 8530)
- Used for document ingestion and retrieval

### Key Integration Points

1. **Model Configuration**: Settings panel → localStorage → agent wrappers → LLM calls
2. **Model Name Format**: Frontend sends `googleai/gemini-2.5-flash`, backend strips prefix
3. **Docker Networking**: Frontend uses `ADK_BASE_URL=http://adkpy:8088` internally
4. **Token Tracking**: Telemetry tool tracks usage across all agents
5. **File Processing**: Assets are enriched with text extraction before AI processing

### Environment Variables

```bash
# Required
GOOGLE_GENAI_API_KEY=your_api_key_here

# ADK/A2A Configuration
ORCH_MODE=adk                    # or "local" for Genkit
ADK_BASE_URL=http://adkpy:8088  # Docker internal URL
NEXT_PUBLIC_ORCH_MODE=adk       # Client-side flag

# Optional
BING_SEARCH_API_KEY=...          # For web search (falls back to DuckDuckGo)
WEB_SEARCH_CACHE=.cache/web-search.json
NEXT_PUBLIC_LOCAL_UPLOADS=true  # Store uploads locally vs Firebase
NEXT_PUBLIC_DISABLE_FIRESTORE=true
```

### Design System

- **Colors**: Deep Navy (#192940), Action Green (#73BF50), Slate Blue (#556273)
- **Typography**: Montserrat (headings), Roboto (body)
- **Spacing**: 8px grid system
- **Components**: shadcn/ui with Radix UI primitives

### Common Issues & Solutions

1. **AI not responding**: Check Docker logs `docker logs presentationpro-adkpy-1`
   - Model name format error: Backend needs to strip "googleai/" prefix
   - API key issues: Verify `GOOGLE_GENAI_API_KEY` is set

2. **Port conflicts**: Frontend MUST use port 3000 (hardcoded)

3. **Docker volume mounts**: Changes to Python code require container restart:
   ```bash
   docker compose restart adkpy
   ```

### Testing Specific Features

```bash
# Test ADK backend health
curl http://localhost:8089/health

# Monitor backend logs
docker logs -f presentationpro-adkpy-1

# Check all services
docker compose ps
```

### Data Flow for Presentation Generation

1. User input → Server action (`src/lib/actions.ts`)
2. Route to ADK backend via orchestrator client
3. Python backend orchestrates agents sequentially
4. Results returned and stored in localStorage
5. UI updates based on state changes

### Important Implementation Details

- Presentation data persists in localStorage as `presentation` object
- Images generated asynchronously after slides
- Context Meter (25-100%) guides clarification depth
- Agent models configurable per-agent in Settings
- File uploads processed for text extraction before AI analysis
- Web search uses cache to reduce API calls
- Use uv for all Python installs and dependencies
- Workflow state tracks execution progress and telemetry
- Graph RAG provides section-specific context for each slide
- Parallel slide generation supported via workflow configuration
- Quality evaluation loops ensure content meets standards
- A2A agent cards enable dynamic capability discovery

## Workflow Development

### Creating New Workflows

```yaml
# adkpy/workflows/custom_workflow.yaml
id: custom_workflow
version: 1.0.0
steps:
  - id: step1
    type: agent|tool|parallel|loop
    name: agent_or_tool_name
    input:
      key: ${inputs.value}  # Reference inputs
      state: ${state.field}  # Reference state
    on_success:
      mutate_state: handler_name  # State mutation
```

### Workflow Patterns

1. **Sequential**: Steps execute in order
2. **Parallel**: Fan-out to multiple agents/tools
3. **Loop**: Iterate until condition met
4. **Conditional**: Branch based on state

### State Management

- Workflow state defined in `schemas/workflow_state.py`
- Mutations handled in `workflows/mutations.py`
- State persists across workflow steps
- Access via `${state.field}` in YAML

## Recent Architectural Improvements

Based on Google ADK Multi-Agent Patterns:

1. **Dynamic Agent Discovery**: A2A cards for runtime capability resolution
2. **Workflow Orchestration**: YAML-driven sequential/parallel/loop patterns
3. **Graph RAG Integration**: ArangoDB as knowledge fabric for presentations
4. **MCP Tool Server**: Centralized tool access via Model Context Protocol
5. **Telemetry-First**: Comprehensive tracking at every orchestration step
6. **Policy Enforcement**: A2A policies for guardrails and token budgets
7. **Graceful Degradation**: Fallback mechanisms for unhealthy agents

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.