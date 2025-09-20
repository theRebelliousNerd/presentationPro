# PresentationPro Agent Operations Guide

> **Editing note:** Never delete existing entries from this guide. Append new instructions so we retain the historical playbook.

## Core Service Ports

| Service | Container | Port |
| --- | --- | --- |
| Next.js UI | `web` | 3000 |
| FastAPI API gateway | `api-gateway` | 18088 (host) -> 8088 |
| Workflow Orchestrator | `orchestrate` | 10000 |
| Clarifier agent | `clarifier` | 10001 |
| Outline agent | `outline` | 10002 |
| Slide writer agent | `slide_writer` | 10003 |
| Critic agent | `critic` | 10004 |
| Notes polisher agent | `notes_polisher` | 10005 |
| Design agent | `design` | 10006 |
| Script writer agent | `script_writer` | 10007 |
| Research agent | `research` | 10008 |
| VisionCV MCP bridge | `visioncv` | 9170 |
| ADK developer UI | `dev-ui` | 8100 |
| ArangoDB | `arangodb` | 8530 |

These ports assume the default Docker Compose topology described in `docs/blueprint.md`.

## Launching the ADK Dev UI

### Preferred: Google ADK CLI

```bash
export GOOGLE_GENAI_API_KEY=YOUR_KEY
python adkpy/launch_dev_ui.py
```

`launch_dev_ui.py` calls `adk web` when the Google ADK CLI is installed, so you get the official UI with agent cards. Override `ADK_DEV_HOST` / `ADK_DEV_PORT` if you need different bindings.

### Fallback: Bundled FastAPI UI

If the CLI is not available the launcher falls back to the lightweight FastAPI UI that ships with the repo. You still need `GOOGLE_GENAI_API_KEY` because the agents pull live models.

## Workflow Card Cheatsheet

Inside the Dev UI you will find a `Presentation Workflow` card (or use the HTTP client tab if you are on the fallback UI). Post to `/v1/workflow/presentation` with a payload like this:

```json
{
  "presentationId": "demo-123",
  "history": [
    { "role": "user", "content": "Build a pitch for our Q4 roadmap." }
  ],
  "initialInput": {
    "text": "Pitch the Q4 roadmap focusing on AI upgrades",
    "audience": "executive",
    "length": "medium"
  },
  "newFiles": []
}
```

The response contains `state`, `final`, `trace`, and a `sessionId`. When the clarifier needs more information you will see `final.status === "needs_clarification"`.

### Resuming a Workflow Session

1. Capture the `sessionId` and `state` (persist `state` to disk if you are iterating).
2. Collect the follow-up answer from the user and append it to `history`.
3. Re-run the same endpoint with the previous `sessionId` *and* the prior `state`:

```json
{
  "presentationId": "demo-123",
  "sessionId": "SESSION_FROM_LAST_CALL",
  "state": { /* state blob from prior response */ },
  "history": [
    { "role": "user", "content": "Build a pitch for our Q4 roadmap." },
    { "role": "user", "content": "Audience wants to see LTV impact." }
  ],
  "initialInput": {
    "text": "Pitch the Q4 roadmap focusing on AI upgrades",
    "audience": "executive",
    "length": "medium"
  }
}
```

The workflow runner will pick up where it left off (outline -> slides -> critic) once the clarifier marks the exchange as finished.

## CLI Automation (no UI)

You can exercise the workflow directly from a terminal. Store your inputs and state in JSON files so you can resume sessions.

```bash
# 1. Start a new run
echo '{
  "presentationId": "demo-123",
  "history": [],
  "initialInput": { "text": "Pitch Q4 roadmap", "audience": "executive" }
}' > inputs.json

curl -s http://localhost:8088/v1/workflow/presentation   -H 'Content-Type: application/json'   -d @inputs.json | tee run-1.json

# 2. Resume after clarifier follow-up
jq '.state' run-1.json > state.json
jq '.sessionId' run-1.json -r > session.txt

curl -s http://localhost:8088/v1/workflow/presentation   -H 'Content-Type: application/json'   -d @<(jq --arg session $(cat session.txt)             --slurpfile state state.json             '(.sessionId=$session) + {state: $state[0], history: (.history + [{"role":"user","content":"Audience cares about LTV"}])}' inputs.json)   | tee run-2.json
```

If you prefer the ADK CLI you can also run:

```bash
adk workflow run adkpy/workflows/presentation_workflow.yaml   --inputs inputs.json   --state-out run-1-state.json
```

Feed `run-1-state.json` back with `adk workflow run --state-in run-1-state.json` (after editing `inputs.json` with the new clarifier answer) to continue the session. The YAML workflow already invokes Graph RAG ingest/retrieve and the slide quality loop.

---

*Last updated: align Dev UI and CLI flows for workflow resume support.*
## Dependency Refresh & Container Rebuild

1. Run `docker compose build api-gateway clarifier outline slide-writer critic notes-polisher design script-writer research orchestrate dev-ui visioncv` to bake the latest uv-powered images (all Dockerfiles now copy the full `adkpy` package so agent imports can reach shared tools).
2. Restart the core stack with `docker compose up -d arangodb visioncv clarifier outline slide-writer critic notes-polisher design script-writer research orchestrate api-gateway dev-ui`.
3. Wait for every container to report `healthy` (`docker compose ps`). The agent health checks now ping their TCP ports via Python `socket.create_connection`, so a green state simply means the service is accepting requests.

## VisionCV + Workflow Validation

- Ensure `VISIONCV_*` flags are set in `.env` before restarting so the design and research agents route through the MCP bridge.
- After the stack is up, confirm the MCP server responds: `curl http://localhost:9170/mcp` should return `406 Not Acceptable` (expected for GET; it proves the HTTP bridge is alive).
- Trigger a quick workflow smoke test:
  ```bash
  echo '{
    "presentationId": "smoke-test-001",
    "history": [],
    "initialInput": {
      "text": "Create a brief deck explaining our VisionCV integration",
      "audience": "product",
      "length": "short"
    },
    "newFiles": []
  }' > workflow-smoke.json

  curl -s http://localhost:18088/v1/workflow/presentation \
    -H 'Content-Type: application/json' \
    -d @workflow-smoke.json | jq '.final.status, .trace[]?.id'
  ```
  A `needs_clarification` status is fine on the first run; capture `sessionId`/`state` to resume once you collect the follow-up input.

## Dev UI Spot Check

- Verify the CLI-backed Dev UI is live with `Invoke-WebRequest -UseBasicParsing http://localhost:8100/` (HTTP 200 = OK).
- Inside the UI, load the *Presentation Workflow* card to confirm the trace table renders and that VisionCV tasks appear when the related env vars are enabled.

_Last validated after uv-based rebuild + VisionCV restart (Sept 20, 2025)._ 
## Design Token Catalog

- Blueprint-approved colors, gradients, patterns, and layout primitives live in `adkpy/config/design_tokens.json`.
- Agents access them via `load_design_tokens()` so LLM tools return both token identifiers and resolved CSS/SVG.
- Update this schema (and token docs) before introducing new visual treatments; session state should reference token IDs instead of raw hex values.

## Workflow Additions

- The presentation workflow now calls the design agent in parallel per slide to assign tokenized backgrounds before critique.
- Critic, notes polisher, and script writer agents run automatically after design so slides ship with QA'd content, refined notes, and a full narrative.
- Auxiliary workflows available: design refresh (`/v1/workflow/design-refresh`), evidence sweep (`/v1/workflow/evidence-sweep`), research prep (`/v1/workflow/research-prep`), and regression validation (`/v1/workflow/regression-validation`).
