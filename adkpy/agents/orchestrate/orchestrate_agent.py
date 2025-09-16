
# Orchestrator service that coordinates presentation agents through the API gateway.

import asyncio
import json
import logging
import os
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class PresentationOrchestrator:
    """Coordinate the presentation workflow by calling the FastAPI gateway."""

    def __init__(self) -> None:
        api_base = (
            os.environ.get("API_GATEWAY_URL")
            or os.environ.get("ADK_BASE_URL")
            or "http://api-gateway:8088"
        )
        self.api_base = api_base.rstrip('/')

    async def _post_json(self, client: httpx.AsyncClient, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.api_base}{path}"
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        try:
            return resp.json()
        except json.JSONDecodeError:
            return {"raw": resp.text}

    async def process_presentation_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        results: Dict[str, Any] = {"status": "processing", "stages": {}}
        presentation_id = request.get("presentationId")
        initial_input: Dict[str, Any] = request.get("initialInput") or {}
        history: List[Dict[str, Any]] = request.get("history") or []
        new_files: List[Dict[str, Any]] = request.get("newFiles") or []
        raw_assets: List[Dict[str, Any]] = request.get("assets") or []

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                clarify_payload = {
                    "history": history,
                    "initialInput": initial_input,
                    "newFiles": new_files,
                    "presentationId": presentation_id,
                }
                clarify_data = await self._post_json(client, "/v1/clarify", clarify_payload)
                results["stages"]["clarification"] = clarify_data

                if not clarify_data.get("finished", True):
                    results["status"] = "needs_clarification"
                    return results

                clarified_content = (
                    clarify_data.get("refinedGoals")
                    or clarify_data.get("clarifiedGoals")
                    or clarify_data.get("response")
                    or ""
                )

                outline_payload: Dict[str, Any] = {
                    "clarifiedContent": clarified_content,
                    "presentationId": presentation_id,
                    "length": initial_input.get("length"),
                    "audience": initial_input.get("audience"),
                    "tone": initial_input.get("tone"),
                    "template": initial_input.get("template"),
                }
                outline_data = await self._post_json(client, "/v1/outline", outline_payload)
                outline_titles: List[str] = outline_data.get("outline", [])
                results["stages"]["outline"] = outline_data

                if not outline_titles:
                    results["status"] = "error"
                    results["error"] = "Outline generation returned no titles."
                    return results

                slide_payload: Dict[str, Any] = {
                    "clarifiedContent": clarified_content,
                    "outline": outline_titles,
                    "audience": initial_input.get("audience"),
                    "tone": initial_input.get("tone"),
                    "length": initial_input.get("length"),
                    "assets": raw_assets,
                    "presentationId": presentation_id,
                }
                slide_data = await self._post_json(client, "/v1/slide/write", slide_payload)
                slides: List[Dict[str, Any]] = slide_data.get("slides", [])
                results["stages"]["slides"] = slide_data

                reviews: List[Dict[str, Any]] = []
                revised_slides: List[Dict[str, Any]] = []
                for idx, slide in enumerate(slides):
                    critique_payload = {
                        "presentationId": presentation_id,
                        "slideIndex": idx,
                        "slide": slide,
                        "audience": initial_input.get("audience"),
                        "tone": initial_input.get("tone"),
                        "length": initial_input.get("length"),
                    }
                    try:
                        critique_data = await self._post_json(client, "/v1/slide/critique", critique_payload)
                        revised_slides.append(critique_data.get("slide") or slide)
                        if critique_data.get("review"):
                            reviews.append(critique_data["review"])
                    except Exception as crit_err:
                        log.warning("Critique failed for slide %s: %s", idx, crit_err)
                        revised_slides.append(slide)
                if reviews:
                    results["stages"]["reviews"] = reviews

                script_payload = {
                    "presentationId": presentation_id,
                    "slides": revised_slides,
                }
                script_data = await self._post_json(client, "/v1/script/generate", script_payload)
                results["stages"]["script"] = script_data

                results["status"] = "complete"
                results["outline"] = outline_titles
                results["slides"] = revised_slides
                results["script"] = script_data.get("script", "")
            except Exception as exc:
                log.error("Workflow error: %s", exc)
                results["status"] = "error"
                results["error"] = str(exc)

        return results


def run_workflow(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience wrapper for synchronous callers."""
    return asyncio.run(PresentationOrchestrator().process_presentation_request(payload))


orchestrator = PresentationOrchestrator()
