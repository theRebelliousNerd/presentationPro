# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Next-Gen Presentation Studio - An AI-powered presentation creation tool that guides users through a multi-step process to create presentations using Google's Agent Development Kit (ADK) and Agent-to-Agent (A2A) protocol.

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

### Dual AI Backend System

The app supports two AI orchestration modes controlled by `ORCH_MODE` environment variable:

1. **`ORCH_MODE=adk`** (ADK/A2A Mode - Current)
   - Uses Python FastAPI backend with Google ADK agents
   - Multi-agent orchestration via A2A protocol
   - Specialized agents: Clarifier, Outline, SlideWriter, Critic, NotesPolisher, Design, ScriptWriter, Research
   - Backend runs on port 8089 (exposed) / 8088 (internal)

2. **`ORCH_MODE=local`** (Genkit Mode - Deprecated)
   - Uses local Genkit flows in `src/ai/flows/`
   - Direct Google Gemini API calls
   - Simpler, single-process architecture

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
- `app/llm.py` - Gemini API wrapper (IMPORTANT: strips "googleai/" prefix from model names)
- `agents/` - Individual agent implementations
- `tools/` - ArangoGraphRAG, WebSearch, Telemetry, AssetsIngest
- `a2a/` - Protocol definitions and policies

**Database**
- ArangoDB for Graph RAG (port 8530)
- Used for document ingestion and retrieval

### Key Integration Points

1. **Model Name Format**: Frontend sends `googleai/gemini-2.5-flash`, backend must strip prefix
2. **Docker Networking**: Frontend uses `ADK_BASE_URL=http://adkpy:8088` internally
3. **Token Tracking**: Telemetry tool tracks usage across all agents
4. **File Processing**: Assets are enriched with text extraction before AI processing

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