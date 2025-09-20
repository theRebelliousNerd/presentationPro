"""Workflow-oriented orchestrator agent for PresentationPro."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, List
from uuid import uuid4

import httpx
from dotenv import load_dotenv

try:
    from config.runtime import get_agent_endpoints
except ImportError:  # pragma: no cover - when running agent standalone
    def get_agent_endpoints() -> Dict[str, str]:
        return {}

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class PresentationOrchestrator:
    """Coordinate the presentation workflow via API gateway while tracking workflow metadata."""

    def __init__(self) -> None:
        agent_endpoints = get_agent_endpoints()
        api_base = (
            os.environ.get("API_GATEWAY_URL")
            or os.environ.get("ADK_BASE_URL")
            or agent_endpoints.get("api-gateway")
            or "http://api-gateway:8088"
        )
        self.api_base = api_base.rstrip("/")
        self.agent_endpoints = agent_endpoints

    async def _post_json(self, client: httpx.AsyncClient, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.api_base}{path}"
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        try:
            return resp.json()
        except json.JSONDecodeError:
            return {"raw": resp.text}

    async def process_presentation_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        results: Dict[str, Any] = {
            "status": "processing",
            "stages": {},
        }
        presentation_id = request.get("presentationId")
        if not presentation_id:
            presentation_id = str(uuid4())
            request["presentationId"] = presentation_id

        initial_input: Dict[str, Any] = request.get("initialInput") or {}
        history: List[Dict[str, Any]] = request.get("history") or []
        new_files: List[Dict[str, Any]] = request.get("newFiles") or []
        raw_assets: List[Dict[str, Any]] = request.get("assets") or []

        # Graph RAG ingestion and seeding
        if new_files:
            ingest_summary = rag_ingest_workflow_tool(presentation_id, new_files)
            results["stages"]["ingest"] = ingest_summary

        seed_query = initial_input.get("text") or initial_input.get("topic") or ""
        rag_seed = None
        if seed_query:
            rag_seed = rag_retrieve_workflow_tool(presentation_id, seed_query, limit=6)
            results["stages"]["ragSeed"] = rag_seed

        workflow_payload = {
            "presentationId": presentation_id,
            "history": history,
            "initialInput": initial_input,
            "newFiles": new_files,
            "assets": raw_assets,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                workflow_result = await self._post_json(client, "/v1/workflow/presentation", workflow_payload)
                results["stages"]["workflow"] = workflow_result.get("trace", [])

                final_payload = workflow_result.get("final") or {}
                workflow_state = workflow_result.get("state") or {}

                results["status"] = "complete"
                results["outline"] = workflow_state.get("outline", {}).get("sections")
                results["slides"] = final_payload.get("slides") or []
                results["script"] = final_payload.get("script", "")
                results["final"] = final_payload
            except Exception as exc:  # pragma: no cover - network fallback
                log.error("Workflow error: %s", exc)
                results["status"] = "error"
                results["error"] = str(exc)

        return results


def run_workflow(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience wrapper for synchronous callers."""
    return asyncio.run(PresentationOrchestrator().process_presentation_request(payload))


orchestrator = PresentationOrchestrator()
