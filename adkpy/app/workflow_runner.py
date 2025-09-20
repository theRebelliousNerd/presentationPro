"""Workflow runner that executes presentation workflows using FastAPI endpoints."""

from __future__ import annotations

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from httpx import ASGITransport
import yaml
from fastapi import FastAPI
from pydantic import BaseModel

from workflows import WORKFLOW_PATHS, PRESENTATION_WORKFLOW_PATH
from workflows.tools import (
    rag_ingest_workflow_tool,
    rag_retrieve_workflow_tool,
    finalize_payload,
    evaluate_quality,
    map_theme_to_design,
    prepare_design_payload,
    prepare_critic_payload,
    prepare_notes_payload,
    select_notes_tone,
    load_slides_from_input,
    collect_regression_metrics,
    prepare_research_summary,
)
from workflows import mutations
from schemas.workflow_state import PresentationWorkflowState

LOG = logging.getLogger(__name__)


class _Resolver:
    """Resolve ${...} expressions within workflow inputs."""

    _pattern = re.compile(r"^\$\{([^}]+)\}$")

    def __init__(
        self,
        *,
        inputs: Dict[str, Any],
        state: PresentationWorkflowState,
        steps_stack: List[Dict[str, Any]],
        item: Any = None,
    ) -> None:
        self.inputs = inputs
        self.state = state
        self.steps_stack = steps_stack
        self.item = item

    def resolve(self, value: Any) -> Any:
        if isinstance(value, str):
            match = self._pattern.match(value)
            if match:
                return self._resolve_path(match.group(1))
            return value
        if isinstance(value, dict):
            return {key: self.resolve(val) for key, val in value.items()}
        if isinstance(value, list):
            return [self.resolve(val) for val in value]
        return value

    def _resolve_path(self, path: str) -> Any:
        root_map = {
            "inputs": self.inputs,
            "state": self.state,
            "item": self.item,
        }
        parts = path.split(".")
        root_key = parts[0]
        if root_key == "steps":
            return self._resolve_steps(parts[1:])
        obj = root_map.get(root_key)
        for part in parts[1:]:
            if obj is None:
                return None
            if isinstance(obj, BaseModel):
                obj = getattr(obj, part, None)
            elif isinstance(obj, dict):
                obj = obj.get(part)
            elif isinstance(obj, list):
                if part.isdigit():
                    idx = int(part)
                    obj = obj[idx] if idx < len(obj) else None
                else:
                    obj = None
            else:
                obj = getattr(obj, part, None)
        return obj

    def _resolve_steps(self, path_parts: List[str]) -> Any:
        key = path_parts[0] if path_parts else None
        if key is None:
            return None
        for ctx in reversed(self.steps_stack):
            if key in ctx:
                obj = ctx[key]
                for part in path_parts[1:]:
                    if obj is None:
                        return None
                    if isinstance(obj, dict):
                        obj = obj.get(part)
                    elif isinstance(obj, list) and part.isdigit():
                        idx = int(part)
                        obj = obj[idx] if idx < len(obj) else None
                    else:
                        obj = None
                return obj
        return None


def _to_plain(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(by_alias=True)
    if isinstance(value, dict):
        return {key: _to_plain(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_to_plain(val) for val in value]
    return value


class WorkflowRunner:
    """Execute the presentation workflow YAML specification against FastAPI endpoints."""

    _TOOL_MAP = {
        "graph_rag.ingest": rag_ingest_workflow_tool,
        "graph_rag.retrieve": rag_retrieve_workflow_tool,
        "workflow.finalize_payload": finalize_payload,
        "workflow.evaluate_quality": evaluate_quality,
        "workflow.map_design_tokens": map_theme_to_design,
        "workflow.prepare_design_payload": prepare_design_payload,
        "workflow.prepare_critic_payload": prepare_critic_payload,
        "workflow.prepare_notes_payload": prepare_notes_payload,
        "workflow.select_notes_tone": select_notes_tone,
        "workflow.load_slides": load_slides_from_input,
        "workflow.collect_regression_metrics": collect_regression_metrics,
        "workflow.prepare_research_summary": prepare_research_summary,
    }

    _AGENT_ENDPOINTS = {
        "clarifier": ("/v1/clarify", False),
        "outline": ("/v1/outline", False),
        "slide-writer": ("/v1/slide/write", False),
        "slide_writer": ("/v1/slide/write", False),
        "design": ("/v1/slide/design", False),
        "critic": ("/v1/slide/critique", False),
        "notes-polisher": ("/v1/slide/polish_notes", False),
        "notes_polisher": ("/v1/slide/polish_notes", False),
        "script-writer": ("/v1/script/generate", False),
        "script_writer": ("/v1/script/generate", False),
        "research": ("/v1/research/backgrounds", False),
        "complete": ("/v1/presentations/{session_id}/complete", True),
    }

    def __init__(self) -> None:
        self.specs: Dict[str, Dict[str, Any]] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()


    def _load_spec(self, workflow_id: str) -> Dict[str, Any]:
        path = WORKFLOW_PATHS.get(workflow_id)
        if path is None:
            path = WORKFLOW_PATHS.get("presentation_workflow") or PRESENTATION_WORKFLOW_PATH
        if path is None or not path.exists():
            LOG.warning("Workflow %s spec not found at %s", workflow_id, path)
            return {}
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    async def run(self, app: FastAPI, inputs: Dict[str, Any]) -> Dict[str, Any]:
        workflow_id = inputs.get("workflowId") or "presentation_workflow"
        spec = self.specs.get(workflow_id)
        if spec is None:
            spec = self._load_spec(workflow_id)
            self.specs[workflow_id] = spec

        session_id = inputs.get("sessionId") or inputs.get("session_id")
        session_key = f"{workflow_id}:{session_id}" if session_id else None

        provided_state = inputs.get("state") or inputs.get("workflowState")
        stored_session: Optional[Dict[str, Any]] = None
        async with self._lock:
            if session_key and session_key in self._sessions and not provided_state:
                stored_session = self._sessions.get(session_key)

        if provided_state:
            state = PresentationWorkflowState.model_validate(provided_state)
            existing_trace = list(stored_session.get("trace", [])) if stored_session else []
        elif stored_session:
            state_payload = stored_session.get("state") or {}
            state = PresentationWorkflowState.model_validate(state_payload)
            existing_trace = list(stored_session.get("trace", []))
        else:
            state = PresentationWorkflowState(
                presentationId=inputs.get("presentationId"),
                history=inputs.get("history") or [],
                audience=inputs.get("initialInput", {}).get("audience"),
                tone=inputs.get("initialInput", {}).get("tone"),
                length=inputs.get("initialInput", {}).get("length"),
            )
            existing_trace: List[Dict[str, Any]] = []

        if inputs.get("presentationId"):
            state.presentation_id = inputs.get("presentationId")
        if inputs.get("history") is not None:
            state.history = inputs.get("history") or []

        initial_input = inputs.get("initialInput") or {}
        if initial_input:
            state.audience = initial_input.get("audience", state.audience)
            state.tone = initial_input.get("tone", state.tone)
            state.length = initial_input.get("length", state.length)

        if not session_id:
            session_id = state.metadata.get("sessionId") or uuid4().hex
            session_key = f"{workflow_id}:{session_id}"
        else:
            session_key = f"{workflow_id}:{session_id}"
        state.metadata["sessionId"] = session_id
        state.final_response = None

        global_steps: Dict[str, Any] = {}
        steps_stack: List[Dict[str, Any]] = [global_steps]
        new_trace: List[Dict[str, Any]] = []

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://workflow.local") as client:
            for step in spec.get("steps", []):
                result = await self._execute_step(step, client, inputs, state, steps_stack)
                step_id = step.get("id", f"step_{len(global_steps)}")
                step_record = {"id": step_id, "type": step.get("type"), "result": _to_plain(result)}
                global_steps[step_id] = {"result": result}
                new_trace.append(step_record)
                if workflow_id == "presentation_workflow" and step_id == "clarify" and not bool(result.get("finished", True)):
                    state.final_response = {"status": "needs_clarification", "clarify": result}
                    break

        combined_trace = existing_trace + new_trace
        LOG.info(
            "Workflow %s session %s executed %d step(s); combined trace length=%d",
            workflow_id,
            session_id,
            len(new_trace),
            len(combined_trace),
        )
        state_dump = state.model_dump(by_alias=True)
        session_snapshot = {
            "state": state_dump,
            "trace": combined_trace,
            "final": state.final_response,
        }
        async with self._lock:
            self._sessions[session_key] = session_snapshot

        return {
            "session_id": session_id,
            "sessionId": session_id,
            "workflowId": workflow_id,
            "state": state_dump,
            "trace": combined_trace,
            "final": state.final_response,
        }



    async def _execute_step(
        self,
        step: Dict[str, Any],
        client: httpx.AsyncClient,
        inputs: Dict[str, Any],
        state: PresentationWorkflowState,
        steps_stack: List[Dict[str, Any]],
        *,
        item: Any = None,
    ) -> Dict[str, Any]:
        resolver = _Resolver(inputs=inputs, state=state, steps_stack=steps_stack, item=item)
        step_type = step.get("type", "agent")
        step_id = step.get("id", "step")

        if step_type == "tool":
            payload = resolver.resolve(step.get("input", {}))
            payload = _to_plain(payload)
            result = self._execute_tool(step, payload)
        elif step_type == "agent":
            payload = resolver.resolve(step.get("input", {}))
            payload = _to_plain(payload)
            result = await self._call_agent(step, payload, client, state)
        elif step_type == "parallel":
            result = await self._execute_parallel(step, client, inputs, state, steps_stack)
        elif step_type == "loop":
            result = await self._execute_loop(step, client, inputs, state, steps_stack)
        else:
            LOG.warning("Unsupported step type '%s' for step %s", step_type, step_id)
            result = {}

        self._apply_mutation(step, result, inputs=inputs, state=state, item=item)
        return result

    def _execute_tool(self, step: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        name = step.get("name")
        func = self._TOOL_MAP.get(name)
        if not func:
            LOG.warning("No tool registered for %s", name)
            return {}
        return func(**payload)

    async def _call_agent(
        self,
        step: Dict[str, Any],
        payload: Dict[str, Any],
        client: httpx.AsyncClient,
        state: PresentationWorkflowState,
    ) -> Dict[str, Any]:
        name = step.get("name")
        endpoint, requires_path = self._AGENT_ENDPOINTS.get(name, (None, False))
        if not endpoint:
            LOG.warning("No endpoint mapping for agent %s", name)
            return {}

        request_payload = payload.copy()
        LOG.info("Calling agent %s with payload keys=%s", name, list(request_payload.keys()))
        if requires_path:
            session_id = (
                request_payload.pop("sessionId", None)
                or request_payload.pop("session_id", None)
                or state.metadata.get("sessionId")
            )
            if not session_id:
                raise ValueError("Session ID required for completion step")
            path = endpoint.format(session_id=session_id)
            response = await client.post(path, json=request_payload or {})
        else:
            response = await client.post(endpoint, json=request_payload)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            LOG.error("Agent %s returned %s: %s", name, exc.response.status_code, exc.response.text)
            raise
        data = response.json()
        if name == "clarifier":
            session_id = data.get("session_id") or data.get("sessionId")
            if session_id:
                state.metadata["sessionId"] = session_id
        return data

    async def _execute_parallel(
        self,
        step: Dict[str, Any],
        client: httpx.AsyncClient,
        inputs: Dict[str, Any],
        state: PresentationWorkflowState,
        steps_stack: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        resolver = _Resolver(inputs=inputs, state=state, steps_stack=steps_stack)
        items = resolver.resolve(step.get("foreach")) or resolver.resolve(step.get("items")) or []
        workflow_spec = step.get("workflow", {})
        sub_steps = workflow_spec.get("steps", [])
        results: List[Dict[str, Any]] = []

        for entry in items:
            local_context: Dict[str, Any] = {}
            steps_stack.append(local_context)
            last_result: Dict[str, Any] = {}
            for sub_step in sub_steps:
                res = await self._execute_step(sub_step, client, inputs, state, steps_stack, item=entry)
                local_context[sub_step.get("id", "step")] = {"result": res}
                last_result = res
            steps_stack.pop()
            results.append({"item": _to_plain(entry), "result": _to_plain(last_result)})

        return {"results": results}

    async def _execute_loop(
        self,
        step: Dict[str, Any],
        client: httpx.AsyncClient,
        inputs: Dict[str, Any],
        state: PresentationWorkflowState,
        steps_stack: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        workflow_spec = step.get("workflow", {})
        sub_steps = workflow_spec.get("steps", [])
        max_iterations = int(step.get("max_iterations", 3))
        condition_expr = step.get("condition")
        iterations: List[Dict[str, Any]] = []

        for iteration in range(max_iterations):
            local_context: Dict[str, Any] = {}
            steps_stack.append(local_context)
            last_result: Dict[str, Any] = {}
            for sub_step in sub_steps:
                res = await self._execute_step(sub_step, client, inputs, state, steps_stack)
                local_context[sub_step.get("id", "step")] = {"result": res}
                last_result = res
            should_continue = False
            if condition_expr:
                resolver = _Resolver(inputs=inputs, state=state, steps_stack=steps_stack)
                should_continue = bool(resolver.resolve(condition_expr))
            steps_stack.pop()
            iterations.append({"iteration": iteration, "result": _to_plain(last_result)})
            if not should_continue:
                break

        return {"iterations": iterations}

    def _apply_mutation(
        self,
        step: Dict[str, Any],
        result: Dict[str, Any],
        *,
        inputs: Dict[str, Any],
        state: PresentationWorkflowState,
        item: Any = None,
    ) -> None:
        on_success = step.get("on_success") or {}
        mutator_name = on_success.get("mutate_state")
        if not mutator_name:
            return
        mutator = getattr(mutations, mutator_name, None)
        if not mutator:
            LOG.warning("Mutation %s not found", mutator_name)
            return
        mutator(state, result, inputs=inputs, item=item)


__all__ = ["WorkflowRunner"]
