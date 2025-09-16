# PresentationPro Codebase Audit

## Overview
This document captures defects and underdeveloped integrations discovered during a deep inspection of the PresentationPro repo. Issues are grouped by severity and reference the relevant files for traceability.

## Critical Issues

### Makefile references missing services
- Files: `Makefile:41-110`, `Makefile:160-188`, `docker-compose.yml`
- Impact: `make build-backend`, `make test`, `make logs-orchestrator`, and `make shell-orchestrator` target an `orchestrator`/`mcp-server` service that no longer exists. Every command fails immediately, so the documented build/test flow is broken out of the box.

### Health checks require unavailable binaries
- Files: `docker-compose.yml:70-361`, `adkpy/Dockerfile`, `adkpy/agents/*/Dockerfile`, `visioncv/Dockerfile`
- Impact: Compose health checks run `curl`/`wget`, but none of the slim Python images install those tools. Containers start but flip to `unhealthy` with exit code 127, causing noisy restarts and false negatives from `make health` until each image packages the requisite binaries.

### Agent model overrides are ignored
- Files: `src/components/app/SettingsPanel.tsx`, `src/lib/agent-models.ts`, `src/lib/orchestrator.ts`
- Impact: Model selections are saved in `localStorage`, yet server actions always call `withAgentModel`, which re-reads models on the server (where `localStorage` is unavailable). Requests fall back to defaults, leaving the Settings UI ineffective.

## High Severity Issues

### Arango autosave appends but never prunes
- Files: `src/lib/arango-client.ts:190-218`, `adkpy/app/arango_routes.py:215-269`
- Finding: `savePresentation` skips `save_*` operations on empty arrays, while backend handlers append new rows. Clearing chat/outline/slides in the UI doesn't remove the prior documents, so autosave accumulates duplicates that reappear on reload.

### Clarified goals lost on reload
- Files: `src/lib/arango-client.ts:233-265`, `adkpy/app/arango_routes.py:257-264`, `src/lib/types.ts`
- Finding: Clarified goals are persisted as a synthetic `CLARIFIED_GOALS:` clarification, but `arangoStateToPresentation` neither strips the sentinel nor sets `presentation.clarifiedGoals`. Reloading reverts to `clarifying` and injects the raw marker into chat history.

### Outline metadata never derives a title
- File: `src/lib/arango-client.ts:284-292`
- Finding: Outline entries are strings, yet `extractTitle` reads `presentation.outline[0].title`, which is always undefined. Presentation listings fall back to `'Untitled Presentation'` even after outlining.

### Duplicated decks keep editing the original
- File: `src/hooks/use-presentation-state-arango.ts:235-250`
- Finding: `duplicatePresentation` writes the clone and updates `localStorage`, but the hook never switches `presentationId` or state. Auto-save continues mutating the source presentation until a full reload.

### Server actions default to unreachable hosts outside Docker
- Files: `src/lib/actions.ts:44-71`, `src/lib/arango-client.ts:11-31`, `src/components/app/PanelController.tsx:49-63`
- Finding: Without `ADK_BASE_URL`/`NEXT_PUBLIC_ADK_BASE_URL`, server actions target `http://api-gateway:8088`, which is only resolvable inside docker. Running via `npm run dev` causes all slide/design/export calls to fail silently.

### Design data is never persisted
- Files: `src/lib/arango-client.ts:202-215`, `adkpy/app/arango_routes.py:233-247`
- Finding: Autosave only posts title/content/notes/image prompt for each slide. Fields such as `designSpec`, `designCode`, `imageUrl`, `useGeneratedImage`, and constraint overrides are dropped. Reloading a deck strips all generated design/layout state, undoing the Design agent's work.

### Initial-input preferences are lost after reload
- Files: `src/lib/arango-client.ts:233-276`, `adkpy/app/arango_routes.py:375-430`, `adkpy/agents/base_arango_client.py:688-739`
- Finding: `initProject` stores the user's initial input under `presentations.preferences`, but subsequent autosaves never update that document, and `arangoStateToPresentation` ignores the stored preferences entirely. After a refresh every presentation reverts to the default blank form, discarding clarifier patches and user selections.

### Full script output is not persisted
### Critic model selection is unused during generation
- Files: `adkpy/agents/wrappers.py:260-310`, `src/lib/orchestrator.ts:52`
- Finding: Frontend calls `withSlideModels` to supply both writer and critic models, but `SlideWriterAgent.run` ignores `criticModel`. Any attempt to change the critic model in Settings has no effect on slide generation or review.
### ScriptWriter ignores supplied assets
- Files: `adkpy/agents/wrappers.py:700-760`
- Finding: The ScriptWriter agent receives `assets` from the UI but never uses them when crafting the presentation script. Supporting documents collected during clarification are therefore absent from the final narration.
### SlideWriter ignores provided context
- Files: `adkpy/agents/wrappers.py:260-331`
- Finding: `SlideWriterAgent.run` never reads `assets`, `constraints`, or `existing` even though they are passed in from the frontend. Uploaded documents, density settings, and previous slide edits are therefore ignored during generation, defeating the refinements gathered during clarification.
### Design variants are never saved
- Files: `src/components/app/editor/design/VariantPicker.tsx`, `src/lib/arango-client.ts:190-218`
- Finding: Editors can preview design variants and apply them to `slide.designSpec`, but autosave only posts basic slide fields. Any adopted design variant is lost on refresh.
- Files: `src/lib/arango-client.ts:190-218`
- Finding: Autosave never includes `presentation.fullScript`, so the script generated by `generateFullScript` disappears on refresh. There is also no backend endpoint handling script storage, meaning the "Generate Full Script" action only lasts for the current session.
### Critic auto-review requires unused `ADK_BASE_URL`
- Files: `adkpy/app/main.py:300-360`
- Finding: The vision-based blur/contrast checks use `_visioncv_call_http` to build `(ADK_BASE_URL or localhost)/v1/visioncv/...`. In Docker, the service is rebroadcast on `http://visioncv:9170/mcp`, so the fallback call hits the API gateway instead of VisionCV and fails. Consequently no auto-issues are attached unless the environment manually reconfigures `ADK_BASE_URL` to point outside the stack.
### Project log viewer depends on sparse logging
- Files: `src/components/app/editor/ProjectLogs.tsx`, `adkpy/app/main.py:180-470`
- Finding: The UI exposes a project log pane, but only a handful of endpoints emit `save_message` calls, and most agents log placeholder strings (e.g., "[no text]"). Script generation, image generation, and ingestion never log, so the panel rarely shows meaningful history—feature feels incomplete.
### Script tab is read-only and unsynced
- Files: `src/components/app/editor/Editor.tsx:208-232`, `src/lib/arango-client.ts`
- Finding: The Script tab updates `presentation.fullScript` in React state but there is no save button, autosave, or export. Once the component unmounts the content is lost, signalling the feature is unfinished.
### Orchestrate agent is a stub and never coordinates services
- Files: `adkpy/agents/orchestrate/simple_orchestrate_agent.py`, `docker-compose.yml`
- Finding: The `orchestrate` service spins up an ADK agent that only simulates workflow in-process. It doesn’t call the microservice agents or handle looping/subtasks, so running it adds no functionality. Complex flows (iterative clarifier loops, parallel design/critic passes) are currently manual and underdeveloped.
### Research helper is disconnected from core workflow
- Files: `src/components/app/editor/ResearchHelper.tsx`, `adkpy/agents/wrappers.py:733-807`
- Finding: Research rules are fetched on demand and optionally inserted into notes, but nothing stores the results, tags slides, or feeds them back into generation. The feature lives off to the side and doesn’t influence Clarifier/SlideWriter decisions.
### Outline agent ignores requested length and tone
- Files: `src/lib/actions.ts:101-108`, `adkpy/agents/wrappers.py:202-226`
- Finding: `getPresentationOutline` only forwards the clarified goals; fields such as `length`, `tone`, and `audience` are discarded. The Outline agent therefore generates the same number of slides regardless of the user’s preferred presentation length.

### Arango RAG uses only BM25 text search
- Files: `adkpy/tools/arango_graph_rag_tool.py:37-132`
- Finding: Retrieval relies solely on ArangoSearch analyzers (BM25/TFIDF). There is no vector store, semantic ranking, or slide-scoped context, limiting relevance especially for large document sets.

### Vision placement recommendations are dropped
- Files: `adkpy/agents/wrappers.py:626-645`
- Finding: When `DESIGN_USE_VISIONCV` is enabled the Design agent attaches `placementCandidates`, but the frontend never reads this field (no references in `src`). Suggested layout hints are ignored.

### Project node/link graph is unused
- Files: `adkpy/app/arango_routes.py:382-430`, `adkpy/agents/base_arango_client.py:706-740`
- Finding: `initProject` seeds `project_nodes` and `project_links`, yet no consumer reads them. The knowledge graph intended to relate assets, templates, and slides remains unexploited.

### Research agent output is transient
- Files: `adkpy/agents/wrappers.py:733-807`, `src/components/app/editor/ResearchHelper.tsx`
- Finding: Research results are returned as ephemeral rules and never persisted in Arango or bound to slides. They can’t inform later generations without manual copy/paste.

### Slide generation runs strictly serially on the client
- Files: `src/app/page.tsx:131-173`
- Finding: Slides are generated in a synchronous loop with `await` per slide. Long outlines freeze the UI; there is no batching, streaming, or background queue to improve throughput.

### Token “Apply to all” stays in local state only
- Files: `src/components/app/editor/Editor.tsx:34-47`
- Finding: Updating design tokens across slides mutates React state but the autosave payload omits token fields, so the styling change disappears on reload.

### Vision-based auto QA disabled by default
- Files: `adkpy/app/main.py:300-347`, `docker-compose.yml`
- Finding: Critic/Design VisionCV hooks depend on env flags (`VISIONCV_AUTO_QA`, `DESIGN_USE_VISIONCV`) that default to `false`; there is no UI toggle. Quality checks remain dormant in most runs.

### Template endpoints lack frontend integration
- Files: `adkpy/app/arango_extras.py:20-38`, `src`
- Finding: `/v1/arango/presentations/{id}/template` exists to record template selection, but no UI calls it. Template metadata and resulting edges sit unused.

### Design “Bake to Image” stays client-side
- Files: `src/components/app/editor/design/DesignPanel.tsx:17-26`, `src/components/app/editor/ImageDisplay.tsx:29-89`
- Finding: Baking a layout renders PNG and uploads it, but the design spec itself isn’t stored server-side. Without persisted layout metadata the baked image can’t be regenerated or audited later.
### Vision contrast overlays are not persisted
- Files: `src/components/app/editor/ImageDisplay.tsx:91-157`
- Finding: Contrast analysis adjusts `overlay` state client-side, but the value is never stored with the slide. Reloading discards the recommended darkening even if VisionCV flagged the slide.

### Asset ingest truncates context aggressively
- Files: `src/lib/ingest.ts:49-98`, `adkpy/tools/arango_graph_rag_tool.py:88-123`
- Finding: Only the first ~4k characters per file and the first 50 paragraphs are ingested. Large PDFs lose most detail and there’s no adaptive chunking per slide.

### No automatic clarifier follow-up when unfinished
- Files: `src/components/app/ClarificationChat.tsx:172-207`
- Finding: When the Clarifier signals `finished: false`, the UI just appends the assistant turn; there is no auto-prompt to continue or queue follow-up questions from the Outline stage.

### Research notes are not surfaced in slide editor
- Files: `src/components/app/editor/ResearchHelper.tsx`, `src/components/app/editor/SlideEditor.tsx`
- Finding: Even after fetching rules, there’s no “insert into slide” workflow. Designers must copy/paste manually into speaker notes.

### Slide critic suggestions aren’t applied
- Files: `src/lib/actions.ts:174-199`, `src/components/app/editor/SlideEditor.tsx`
- Finding: Critic responses include `_review` with `issues`/`suggestions`, but there’s no UI to accept fixes. Auto-apply pipelines (looping until clean) are absent.

### No cross-slide consistency checks
- Files: `adkpy/agents/wrappers.py:260-607`
- Finding: Each slide is generated independently; there’s no agent pass ensuring consistent terminology, length, or design tokens across the deck.

### Arango design rules are static
- Files: `adkpy/app/design_rules.py`
- Finding: Design heuristics are seeded once and never updated with telemetry. There’s no mechanism to store user overrides or learn preferences from saved decks.

### Vision agent limited to HTTP transport
- Files: `visioncv/Dockerfile`, `visioncv/visioncv/agent.py`
- Finding: The MCP server is always launched with `--transport http`. STDIO/SSE transports required for agent chaining are unimplemented, limiting reuse outside Docker.

### Asset categories don’t sync with clarifier intents
- Files: `src/components/app/ClarificationChat.tsx:146-190`, `adkpy/tools/assets_ingest_tool.py`
- Finding: Clarifier reclassifies files into content/style/graphics, but Arango `assets` records retain the original upload category. Downstream agents can’t rely on the curated intents.

### No slide-to-asset link after design usage
- Files: `adkpy/app/arango_extras.py:40-74`, `src/components/app/editor/ImageDisplay.tsx`
- Finding: An endpoint exists to call `use-asset`, yet the design/image flows never invoke it. Arango can’t tell which assets appear on which slide.
### Telemetry lacks central aggregation
- Files: `src/lib/token-meter.ts`, `adkpy/tools/telemetry_tool.py`
- Finding: Frontend tracks usage in localStorage and MCP tools write JSONL locally, but nothing aggregates telemetry for presentation-level reporting. There’s no Arango schema capturing per-agent duration, tokens, or errors to visualize.
### Per-agent telemetry is inconsistent
- Files: `adkpy/tools/telemetry_tool.py`, `adkpy/agents/wrappers.py`, `adkpy/a2a/messages.py`
- Finding: Some wrappers call the telemetry tool, others skip it, and there’s no trace/span propagation across agents. You cannot reconstruct end-to-end flows or visualize agent timelines from the stored data.
### No user-facing telemetry dashboard
- Files: `src/components`, `adkpy/tools/telemetry_tool.py`
- Finding: Telemetry events are written to local JSONL files or stored client-side, but no UI or API aggregates them. Product owners cannot inspect token spend per agent, execution latency, or usage trends.
## Medium Severity Issues

### Review drawer fetches 404 during local dev
- File: `src/components/app/PanelController.tsx:49-92`
- Finding: The review panel uses the same base-URL fallback as server actions, so it points to the Next.js server when docker isn't used. Every fetch returns 404, hiding critic history.

### Un-sanitized SVG uploads
- File: `src/app/api/upload/route.ts:23-57`
- Finding: SVG files are written verbatim to `public/uploads` and served back without sanitization, enabling an XSS vector.

### Reset flow fires racey background saves
- File: `src/hooks/use-presentation-state-arango.ts:205-220`
- Finding: `resetState` kicks off two asynchronous `savePresentation` calls without awaiting them and flips `isLoaded` to true immediately, risking lost writes or partial state.

### VisionCV tool list out-of-sync
- Files: `visioncv/server.py`, `src/app/dev/visioncv/page.tsx`
- Finding: The JSON-RPC `list_tools` response omits newer MCP tools, and the dev UI relies on a static whitelist. Newly added tools remain invisible until both sources are manually updated.

### Asset registration silently fails outside Docker
- Files: `src/app/api/upload/route.ts:45-55`
- Finding: The upload API posts to `${base}/v1/arango/assets/register`, but when `ADK_BASE_URL`/`NEXT_PUBLIC_ADK_BASE_URL` are unset (typical `npm run dev`), `base` becomes an empty string and the request hits `/v1/...` on the Next.js server, returning 404. Asset metadata is never registered, breaking downstream graph links, even though the call fails quietly.

## Suggested Fixes
- Update Make targets to the current service names (`api-gateway`, etc.) and ensure a real `npm test` script exists.
- Install `curl`/`wget` or swap health checks for Python-based probes inside every container.
- Redesign Arango batch writes to delete missing data before re-inserting, making autosave idempotent.
- Parse `CLARIFIED_GOALS` back into `presentation.clarifiedGoals` and normalize chat roles to `'model'` for rendering.
- Treat outline entries as strings when inferring metadata titles.
- Switch hook state to the new ID immediately after duplication.
- Persist agent model selections server-side (e.g., via Arango) or post them with each server action request.
- Provide explicit base URL fallbacks that work both inside and outside docker (`http://localhost:18088`), and guard reset writes with `await`.
- Sanitize SVG content (or block it) before saving.
- Keep VisionCV tool descriptors in sync with the MCP manifest.
- Persist slide design artifacts (design specs, generated images, constraint overrides) alongside slide content.
- Hydrate `presentation.initialInput` from stored preferences and update the metadata document whenever preferences change.
- Ensure asset metadata registration hits the correct gateway host in all environments.
