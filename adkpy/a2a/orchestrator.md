# Orchestrator (ADK/A2A) – Architecture Notes (No Code)

- Role: Sequence agents, enforce A2A policies, collect telemetry, and expose stable HTTP endpoints to the web app.
- Flow (happy path): Clarifier → Outline → (per slide) Retrieve → SlideWriter → Critic loop → Design → ScriptWriter.
- Streaming: Optional SSE for progress updates per trace.
- Error handling: Surface actionable messages; store diagnostics.
- Security: Validate inputs, sanitize text, rate-limit, and log provenance.

This document describes the orchestrator; implementation to be added later using ADK primitives.

