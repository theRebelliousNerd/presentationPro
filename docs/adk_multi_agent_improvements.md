# Applying Google ADK Multi-Agent Patterns to PresentationPro

## 1. Instavibe Multi-Agent Codelab (Step 10 - Orchestrator Agent as A2A Client)

**Key ideas from the codelab**
- The orchestrator runs locally (via ADK Dev UI) while remote specialist agents (Planner, Platform, Social) live on Cloud Run; the parent agent uses **A2A Agent Cards** to discover, register, and route to those services dynamically.
- Remote endpoints are enumerated via `REMOTE_AGENT_ADDRESSES`, but the orchestrator does not hard-code RPC shapes. Instead, it uses `A2ACardResolver` to pull each agent's schema/tooling and caches connection metadata during start-up.
- The orchestrator's workflow is telemetry-rich: each delegation step logs intent (for example, `STEP 3.x: Attempting connection to ...`), records card fetch failures, and publishes a consolidated timeline back to Dev UI for inspection.

**How this can elevate PresentationPro**
- **Dynamic remote discovery:** Rather than hard-coding `/v1/clarify`, `/v1/outline`, etc., we can let the orchestrator resolve each microservice's A2A card at runtime. This buys us versioned contracts, richer metadata (capabilities, expected inputs, rate limits), and easier blue/green deploys.
- **Dev UI parity:** The codelab's orchestrator is designed to run inside the ADK Dev UI. Adopting the same pattern ensures our local debugging faithfully mirrors production orchestration (no more divergence between `python -m agent` and ADK CLI).
- **Telemetry-first workflow:** Instrument the orchestrator with step-level logging tied to card IDs, agent latency, Graph RAG fetch counts, and failure modes. Those traces can surface in both Dev UI and centralized telemetry, giving us quick visibility into pipeline regressions.
- **Graceful degradation:** If card resolution fails (agent down or schema mismatch), the codelab example falls back to informative errors. We should adopt similar guardrails so the orchestrator can decommission or skip unhealthy agents rather than crashing.

**Action experiments**
1. Refactor `PresentationOrchestrator` to pull `REMOTE_AGENT_ADDRESSES` from config, loop through them with `A2ACardResolver`, and cache the returned `AgentCard`.
2. Replace direct FastAPI calls with A2A `invoke` calls derived from the card metadata (tools + schemas). Retain HTTP fallbacks temporarily to smooth the migration.
3. Thread step telemetry (start/finish timestamps, outcome, downstream agent version, RAG chunk usage) into our existing logging/telemetry tooling.

---

## Current Wiring Progress

- Implemented the workflow runner in the API gateway that reads the YAML spec (now including parallel section context and a guardrail loop) and orchestrates clarify -> outline -> slides -> completion using existing endpoints.
- Workflow state is captured via `PresentationWorkflowState`, persisted back into session storage/telemetry, and the orchestrate service now delegates to `/v1/workflow/presentation`.
- Graph RAG ingest/retrieve tools run as part of the flow; quality evaluation telemetry is stored on the workflow state for inspection in the Dev UI.
- Added server-side `runPresentationWorkflow` action and `orchWorkflowPresentation` client helper so the Next.js UI now routes clarify/outline/slide generation through the same workflow path.
- Dev UI users can hit `/v1/workflow/presentation` to see the trace; when the clarifier still needs more info the workflow returns `needs_clarification` instead of running downstream steps.

## 2. ADK Workflow Agents Guide (Sequential, Loop, Parallel)

Google's workflow-agent docs outline three complementary orchestration patterns:
- **Sequential agents** ([docs](https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/)) execute steps in order, sharing state via `WorkflowState` while supporting per-step retries, guardrails, and adapters.
- **Loop agents** ([docs](https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/)) repeatedly execute a step or sub-workflow until a stop condition or max loop count is reached. They include evaluation hooks to decide whether to continue iterating.
- **Parallel agents** ([docs](https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/)) fan out work to multiple steps concurrently, aggregate the responses, and optionally reconcile or reduce the outputs.

**How this can elevate PresentationPro (with Graph RAG at the center)**
- **Sequential spine for the presentation journey:** Model clarify -> outline -> slide writing -> critique -> script -> research as a `SequentialWorkflowAgent`. Inject Graph RAG retrieval at each hand-off so the state object carries the relevant chunks (clarify uses it for audience context, outline for structure, slide writer for per-section grounding).
- **Looped critique gated by RAG signal:** Wrap the critic pass in a `LoopWorkflowAgent` so we re-run critique + slide updates until the evaluator confirms the slide aligns with Graph RAG-sourced facts or we hit a max iteration count.
- **Parallel slide generation with shared RAG cache:** Use a `ParallelWorkflowAgent` to spawn slide-writing jobs per outline section. Each worker pulls the section-specific RAG chunks (precomputed in the sequential step) to generate content concurrently while respecting token budgets.
- **Guardrail steps informed by RAG:** Embed `GuardrailTool` calls inside the workflow (e.g., check that every slide cites at least one retrieved chunk, verify accessibility metrics for referenced assets) so Graph RAG data becomes a first-class gate, not an optional hint.

**Action experiments**
1. Describe the end-to-end workflow in YAML/JSON using `SequentialWorkflowAgent`, referencing sub-workflows (loop, parallel) where appropriate.
2. Extend the shared workflow state schema to carry `rag_context` (per slide, per presentation) so each agent step receives the exact chunks it needs without re-querying.
3. Register Graph RAG ingestion/retrieval as workflow tools (e.g., `graph_rag.ingest`, `graph_rag.retrieve`) so steps can call them declaratively instead of ad-hoc Python code.
4. Instrument per-step telemetry to capture RAG latency, chunk counts, and hit ratios, mirroring the workflow docs' guidance on metrics hooks.

---

## 3. Multi-Agent Hierarchy Guide (Parent + Sub-Agent Patterns)

**Key ideas from the hierarchy docs**
- ADK endorses a **hierarchical structure**: a parent agent (orchestrator) owns the conversation and delegates to specialized sub-agents. Sub-agents expose capabilities via **Tools** or **A2A endpoints**.
- Agent hierarchies formalize **capability routing**: the parent inspects the user goal, then selects the best sub-agent (or combination) based on declared skills.
- Sub-agents can themselves embed micro-workflows, enabling multi-level delegation (e.g., a "Research" parent agent choosing among web search, RAG, or vision MCP tools).
- The guide stresses **consistent schemas and guardrails**: shared types, policy enforcement, and structured memory/state to prevent context leakage.

**How this can elevate PresentationPro**
- **Clear capability registry:** Define each agent's exported tools (clarifier, design, research, Graph RAG retrieval) in a manifest so the orchestrator routes by capability rather than fixed endpoints. Include metadata for which steps require RAG support.
- **Nested orchestration:** Allow the Research agent to orchestrate its own sequential loop (RAG search -> web augmentation -> summarization) while exposing a single capability back to the parent.
- **Policy uniformity:** Propagate A2A policies (guardrails, token budgets, safety filters) from parent to sub-agents so we enforce consistent constraints while handling sensitive uploaded assets via Graph RAG.
- **Schema discipline:** Align request/response models between frontend, FastAPI gateway, ADK workflow configs, and Graph RAG schemas so agent cards remain accurate and the Dev UI can auto-generate correct forms.

**Action experiments**
1. Create an **agent capability manifest** (JSON/YAML) that maps each agent to the tools it provides; include Graph RAG ingestion/retrieval as shared tools and annotate which agents depend on them.
2. Encapsulate multi-step agent logic (e.g., Research, Design) into their own workflow agents that the parent orchestrator treats as single capabilities, ensuring Graph RAG usage is consistent across sub-agents.
3. Update our A2A policy and FastAPI routers in tandem to reflect the parent/sub-agent contract-mirroring the guide's examples for context isolation, while providing Graph RAG access only to agents with the right permissions.

---

## 4. Graph RAG-First Integration Strategy

**Objectives**
- Treat Arango Graph RAG as the canonical knowledge fabric for every presentation.
- Ensure ingestion, retrieval, and chunk selection happen inside the workflow layer (not ad-hoc service calls).
- Make RAG observability (chunk provenance, freshness, latency) a first-class signal for orchestration decisions.

**Ingestion pipeline**
- Trigger `ArangoGraphRAGTool.ingest` in the sequential workflow immediately after clarify uploads or whenever new assets arrive. Wrap ingestion in a transactional workflow step so failures bubble up cleanly.
- Extend the ingest step to attach metadata (tone, audience, topic) so downstream retrieval can weight results appropriately. Update Arango indexes if we need facet filters.
- Add pre-ingest processing inside the Research agent to normalize file types (OCR, vision MCP) before handing content to the RAG tool.

**Retrieval pattern across agents**
- Clarifier: seed the conversation with `retrieve(presentationId, initial question)` to surface prior art or conflicting goals.
- Outline: run parallel retrieval per proposed section title to ground structure in existing material.
- Slide Writer: call `retrieve` with section-specific queries; combine top chunks with templating hints (design tokens, blueprint constraints) before generation.
- Critic loop: verify each slide's claims by re-querying RAG and flagging slides that lack supporting chunks.
- Script Writer & Notes Polisher: aggregate slide-specific chunks into a narrative context, reusing cached retrievals to avoid redundant queries.
- Research: orchestrate a hybrid loop (RAG first, then external search if recall is low) and feed successful findings back into the Graph RAG store for future steps.

**Workflow integration tactics**
- Register Graph RAG tools in the workflow agent registry so sequential/parallel/loop steps can invoke them declaratively (`tools: [graph_rag.retrieve]`).
- Cache retrieval results in the workflow state (per slide, per role) to share across sequential and parallel steps without repeated database calls.
- Use workflow guards to ensure each slide references at least one RAG chunk; if not, trigger a loop iteration that re-prompts the slide writer with the missing context.
- Combine parallel slide generation with a reducer step that deduplicates or reorders RAG references before final assembly.

**Observability & safety**
- Emit telemetry for ingestion (documents, chunks, errors), retrieval (latency, chunk counts, coverage), and workflow loops (iterations triggered by missing RAG evidence).
- Enforce size limits and sanitization before ingestion; ensure RAG outputs respect privacy policies by filtering sensitive chunks when agents lack clearance.
- Add quality metrics: percentage of slides with RAG citations, average critic iterations, retrieval precision/recall proxies.

---

## Cross-Cutting Improvements & Roadmap

1. **Package + Path Hygiene**
   - Adopt the codelab's project layout so `adk web` can load every agent without manual `PYTHONPATH` hacks: install agents as a package (`pip install -e adkpy`) or adjust `launch_dev_ui.py` to wrap `adk web` with the correct path.

2. **Unified Config Story**
   - Centralize agent addresses, ports, capabilities, and Graph RAG settings in a single config resource (consumed by Docker Compose, the orchestrator workflow, and the Dev UI). This matches the codelab's bootstrapping scripts and reduces drift.

3. **Enhanced Dev UI Workflows**
   - Leverage workflow agent telemetry to surface per-step progress, RAG coverage, token budgets, and errors in the Dev UI. Provide curated eval sets (as shown in the codelab) to regression-test clarify -> outline -> critic flows with RAG assertions.

4. **Progressive Refactor Plan**
   - Phase 1: Introduce A2A card resolution in our current orchestrator (minimal surface change) and expose Graph RAG tools via A2A.
   - Phase 2: Rebuild the presentation flow as a `SequentialWorkflowAgent`, still invoking existing microservices, with RAG ingestion/retrieval modeled as workflow steps.
   - Phase 3: Layer in loop and parallel sub-workflows (critic loop, slide fan-out) while instrumenting RAG telemetry and guardrails.
   - Phase 4: Collapse duplicated FastAPI orchestrator logic, letting the workflow agent drive both API responses and Dev UI runs, and expand to nested hierarchies (research/design) with Graph RAG-powered decision making.

By centering the refactor on workflow agents and Arango Graph RAG, we can evolve PresentationPro from hand-wired HTTP sequencing into a declarative, observable ADK system where every stage is grounded in indexed user artifacts, scales through parallelism, and stays aligned with the product blueprint's design and trust requirements.

## Implementation Backlog

- Define a sequential workflow config (YAML/JSON) that maps clarify -> outline -> slide writer -> critic loop -> script -> research with Graph RAG steps declared explicitly.
- Wrap critic evaluation in a LoopWorkflowAgent definition and surface stop conditions tied to RAG verification metrics.
- Prototype a ParallelWorkflowAgent that fans out slide-writing per outline section while sharing cached Graph RAG chunks.
- Register graph_rag.ingest and graph_rag.retrieve as reusable workflow tools and update agents to call them through the workflow layer.
- Extend workflow state schemas to cache per-slide rag_context and persist it through API responses.
- Refactor PresentationOrchestrator to prefer A2A card resolution and invoke agents via their declared capabilities.
- Build an agent capability manifest (JSON/YAML) that lists tools, ports, and Graph RAG permissions for each agent.
- Centralize config for agent URLs, ports, and RAG settings so Docker Compose, workflows, and Dev UI share one source of truth.
- Update launch_dev_ui.py (or packaging) so adk web loads agents without manual PYTHONPATH edits.
- Add workflow guardrail steps that fail when slides or scripts lack supporting RAG evidence or break design constraints.
- Instrument telemetry for ingestion counts, retrieval latency, chunk coverage, and workflow iteration counts; surface in Dev UI.
- Expand research agent into a nested workflow that alternates Graph RAG retrieval with external search when recall is low.
- Create regression eval sets (clarify -> outline -> critic) that assert Graph RAG grounding and wire them into Dev UI tests.
- Document required container rebuild/restart steps and blueprints updates for the workflow migration.

## Deployment Notes

- Run docker compose build orchestrate script-writer api-gateway after workflow changes.
- Restart live services with docker compose up -d orchestrate script-writer api-gateway dev-ui.
- Update docs/blueprint.md summaries when workflow guardrails or design rules change.
- Ensure ARANGODB_URL, ARANGODB_DB, and related env vars are defined in .env to satisfy Graph RAG tools.

## Dev UI Usage

- Hit `/v1/workflow/presentation` from the Dev UI (or cURL) to drive the same pipeline the orchestrator runs; the response includes `state.final_response` and a `trace` array for inspection.
- When the clarifier still needs more details the endpoint returns `{ "status": "needs_clarification" }` in `final`, mirroring the conversation cycle in the UI.
- Once clarifier requirements are satisfied the outline, slides, and script are returned in the same payload so you can review quality telemetry (see `state.metadata.quality`).


## Dev UI / CLI workflow alignment

- Added a persistent `AGENTS.md` playbook so everyone has the Docker port map plus copy-paste payloads for `/v1/workflow/presentation`.
- Documented how to launch the ADK Dev UI (CLI-first, FastAPI fallback) and how to post new or resume requests with `sessionId` + `state`.
- Provided curl and `adk workflow run` examples so CLI users can resume the same workflow session without using the UI.
- Dev UI card surfaces the workflow trace; when `final.status === needs_clarification` the runner halts and waits for a follow-up answer.
