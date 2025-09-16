# Repository Guidelines

## Product Vision
Gemini Presentation Studio streamlines the path from raw brief to exportable deck. Contributors extend an experience where users ingest PDFs, docs, or text, clarify intent through conversational AI, approve an outline, and watch slides, speaker notes, and bespoke imagery materialize. Every feature should reinforce fast iteration, trustworthy AI assistance, and professional design guardrails defined in `docs/blueprint.md` (slate blue #778DA9, light gray #E0E1DD, warm beige #FFECD1, Space Grotesk/Inter typography).

## Core Frameworks & Protocols
- **Google Agent Development Kit (ADK):** Python agents in `adkpy/agents/` encapsulate clarify, outline, slide-writing, critic, notes-polisher, design, script-writer, and research behaviors. ADK supplies tool execution, prompt templating, and state passing across turns.
- **Agent-to-Agent (A2A) Protocol:** Policies in `adkpy/a2a/` define message schemas, routing, and guardrails so specialized agents collaborate without leaking context. When you add skills, update the A2A policy and corresponding FastAPI routers.
- **Anthropic Model Context Protocol (MCP) via FastMCP:** `adkpy/tools/mcp_server/` exposes external tools (vision, telemetry, assets ingest) over MCP. FastMCP handles the transport; tool wrappers translate MCP JSON into ADK tool calls and enforce rate limits.
- **FastAPI Orchestrator:** `adkpy/app/main.py` exposes `/v1/clarify`, `/v1/outline`, `/v1/slide`, etc. It strips the `googleai/` prefix from model names per `adkpy/app/llm.py`, manages auth, and streams agent output back to the frontend. New endpoints must align with A2A message contracts.
- **Next.js 15 Frontend:** `src/app/page.tsx` coordinates presentation state, server actions in `src/lib/actions.ts` proxy to the ADK backend, and shadcn/ui + Tailwind implement the UI. Use React Server Components prudently—critical mutate operations live in server actions to protect secrets.
- **ArangoDB Graph RAG:** Tools under `adkpy/tools/arango_graph_rag_tool.py` ingest uploaded artifacts, chunk them, and provide retrieval vectors for agents. Keep schema migrations synchronized with `adkpy/app/db.py` helpers.

## Computer Vision MCP Integration
- **OpenCV MCP Blueprint:** See `docs/Designing OpenCV MCP Tools for Agents.md` for the dedicated microservice roadmap. The goal is to elevate DesignAgent, CriticAgent, and ResearchAgent with objective visual intelligence—palette extraction, layout scoring, accessibility checks, OCR, and chart digitization.
- **Architecture:** The service operates as a stateless MCP server speaking JSON-RPC (`list_tools`, `call_tool`). FastMCP hosts the bridge inside `adkpy/tools/mcp_server/`, mediating between ADK agents and the OpenCV routines. Agents pass base64 assets and tool parameters; results stream back as structured JSON with no persisted session data.
- **Key Tool Families:**
  - *Design intelligence:* brand palette extraction, procedural background synthesis, composition heuristics.
  - *Critic/QA:* brightness/noise metrics, color-contrast accessibility checks, slide layout scoring.
  - *Research extraction:* OCR pre-processing (thresholding, deskew, denoise), chart/graph fingerprinting, data point extraction.
  Extend schemas in the MCP manifest when adding capabilities and ensure corresponding validation lives in both FastAPI and ADK tool wrappers.
- **Deployment:** Containers under `visioncv/` provide the reference FastMCP + OpenCV stack. Use `docker compose up visioncv api-gateway` (or `make visioncv-up`) to launch locally. Coordinate with research before changing the shared Dockerfile or Python dependencies—performance tuning (GPU, SIMD) happens there.
- **Security & Isolation:** MCP servers see only the payloads necessary for a tool invocation. Enforce size limits, sanitize inputs, and avoid returning raw image bytes unless essential. Telemetry hooks should log aggregate usage without leaking image contents.

## Service Topology & Repository Layout
- `src/`: Next.js client + server actions. Key folders: `components/app/` (clarification chat, outline approval, editor), `hooks/` (localStorage + Arango persistence), `lib/` (orchestrator client, agent model registry, token meter).
- `adkpy/`: FastAPI application, ADK agents, MCP tool server, schemas, and tests. Ensure Python code stays hot-reload-friendly inside Docker.
- `visioncv/`: Experimental computer-vision microservice coordinated through docker compose; coordinate with research before changes ship.
- `e2e/`: Playwright regression suites that replicate the clarify -> approve -> edit journey and VisionCV panel flows.
- `docs/`: Product and architecture briefs; update `docs/blueprint.md` when altering UX pillars.
- Ops assets: `docker-compose.yml`, `docker-compose.dev.yml`, `Makefile`, and environment templates orchestrate microservices through Docker Desktop.

## Docker Desktop Service Map
- `web` (Next.js UI) maps `3000:3000` and serves the client; mounts `uploads-data` for public assets and joins `frontend-network` plus `backend-network`.
- `api-gateway` (FastAPI ADK facade) exposes `18088:8088`, strips model prefixes, and brokers calls to agents, Arango, and VisionCV.
- `orchestrate` coordinates agent sequencing at `10000:10000`, forwarding requests to the specialized services described below.
- Agent endpoints publish health checks and JSON APIs on dedicated ports: clarifier `10001`, outline `10002`, slide-writer `10003`, critic `10004`, notes-polisher `10005`, design `10006`, script-writer `10007`, research `10008`.
- `visioncv` (FastMCP + OpenCV) runs on `9170:9170` with the `/mcp` path; toggle usage via `DESIGN_USE_VISIONCV` and related env flags.
- `dev-ui` (ADK developer console) is available at `8100:8100` for agent debugging.
- `arangodb` binds `8530:8529`; credentials derive from `ARANGO_ROOT_PASSWORD` and data persists via `arangodb-data` / `arangodb-apps` volumes.
- Networks: `frontend-network` isolates UI traffic, `backend-network` links Python services, and `database-network` secures database access.
- Persisted volumes: `uploads-data` (user uploads), `arangodb-data`, and `arangodb-apps`; back them up before destructive operations.
## Local Orchestration & Development Flow
1. **Bootstrap:** Copy `.env.example` to `.env` and supply `GOOGLE_GENAI_API_KEY`, `ORCH_MODE=adk`, `ADK_BASE_URL=http://adkpy:8088`, and optional search keys.
2. **Bring up services:** Use `docker compose up --build` for the full stack or scope to `web adkpy arangodb` when iterating on core flows. Docker Desktop should allocate sufficient CPU/RAM (baseline 6 cores/8 GB shared across services).
3. **Quick cycle:** `make quick-dev` builds, starts services, and runs health checks; `make down` handles teardown. Restart individual services after Python or dependency edits: `docker compose restart adkpy` or `docker compose restart web`.
4. **Hot reload tips:** Frontend turbopack automatically reloads; backend reload relies on volume mounts. When touching agent registries or MCP tool wrappers, rebuild the relevant container.

## Coding Standards & Naming
- Follow repo ESLint and TypeScript configuration: 2-space indentation, hook rules, explicit return types for server actions, and consistent Tailwind ordering (see `tailwind.config.ts`).
- React components and hooks use `PascalCase`/`use*`, utilities stay `camelCase`, shared constants prefer SCREAMING_SNAKE_CASE, and new files default to kebab-case.
- Keep shared type definitions synchronized between `src/lib/types.ts`, `adkpy/schemas/`, and any API responses. Update `src/lib/agent-models.ts` when changing model variants or temperature defaults.
- Python code follows Black formatting (though not enforced automatically); prefer type hints and `pydantic` models for request/response validation.

## Testing & Quality Gates
- **Containerized test suite:** `make test` runs `npm test` and `pytest adkpy/tests` inside running containers so results match CI. Ensure ArangoDB is seeded if your tests depend on data.
- **Playwright end-to-end:** Execute `docker compose run --rm web npx playwright test` for regressions across clarify, outline approval, and editor flows. Keep selectors aligned with `data-testid` attributes in `src/components/app/`.
- **Backend unit/integration:** Targeted runs like `docker compose exec adkpy pytest tests/test_outline_agent.py` are encouraged before PRs. Mock outbound calls (Gemini, MCP tools) and assert token telemetry via `adkpy/tools/telemetry` helpers.
- **Performance checks:** When modifying orchestrator code, monitor token and latency metrics via telemetry logs. Capture command output or screenshots and embed them in PRs for reviewer context.

## Data, Security & Configuration Practices
- Secrets live only in `.env` or Docker secrets; never commit keys. `NEXT_PUBLIC_*` variables must remain non-sensitive.
- Uploaded assets persist via Arango-backed storage; ensure new ingestion pathways sanitize HTML/Markdown and respect file size constraints.
- Telemetry aggregates token usage per agent; extend it carefully to avoid logging sensitive payloads. Review `adkpy/tools/telemetry` before emitting new fields.
- Network egress from containers should respect corporate policy; configure proxy variables inside Docker only if required.

## Commit & Pull Request Workflow
- Follow `<type>(scope): summary` conventions (`feat(dev)`, `fix(outline)`, `chore(docs)`, etc.). Squash exploratory commits before requesting review.
- PR descriptions outline motivation, affected services, docker commands run, tests executed, blueprint or schema updates, and any required follow-up ops (e.g., `docker compose restart adkpy`).
- Link relevant docs (`docs/blueprint.md`, ADK guides) and attach verification artifacts—terminal output, screenshots, or log excerpts—especially for UX changes.
- Coordinate cross-service changes (frontend + backend + MCP) via draft PRs to avoid drift in message contracts.

## Reference Checklist for New Contributions
- [ ] Synced product intent with `docs/blueprint.md` and design palette.
- [ ] Updated ADK agent configs, A2A policies, and FastAPI routes together.
- [ ] Exercised containerized unit tests plus Playwright flow relevant to the change.
- [ ] Documented env or migration steps and noted container restarts.
- [ ] Captured telemetry or UI evidence to support reviewer validation.


