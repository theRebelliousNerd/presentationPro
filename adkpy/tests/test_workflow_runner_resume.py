import sys
import types

if 'arango' not in sys.modules:
    arango_mod = types.ModuleType('arango')

    class _DummyArangoClient:
        def __init__(self, *args, **kwargs):
            pass

    arango_mod.ArangoClient = _DummyArangoClient
    sys.modules['arango'] = arango_mod

if 'google.generativeai' not in sys.modules:
    google_pkg = sys.modules.setdefault('google', types.ModuleType('google'))
    generativeai_mod = types.ModuleType('google.generativeai')

    class _DummyGenerativeModel:
        def __init__(self, *args, **kwargs):
            pass

        def generate_content(self, *args, **kwargs):
            class _Resp:
                text = ''
                candidates = []
            return _Resp()

    def _dummy_configure(**kwargs):
        return None

    generativeai_mod.configure = _dummy_configure
    generativeai_mod.GenerativeModel = _DummyGenerativeModel
    google_pkg.generativeai = generativeai_mod
    sys.modules['google.generativeai'] = generativeai_mod

if 'adkpy.tools' not in sys.modules:
    tools_pkg = types.ModuleType('adkpy.tools')

    class _DummyRagTool:
        def ingest(self, *args, **kwargs):
            return {"ingested": True}

        def retrieve(self, *args, **kwargs):
            return {"chunks": []}

    tools_pkg.ArangoGraphRAGTool = _DummyRagTool
    tools_pkg.Asset = dict
    tools_pkg.IngestResponse = dict
    tools_pkg.RetrieveResponse = dict
    tools_pkg.RetrievedChunk = dict
    sys.modules['adkpy.tools'] = tools_pkg

    rag_mod = types.ModuleType('adkpy.tools.arango_graph_rag_tool')
    rag_mod.ArangoGraphRAGTool = _DummyRagTool
    rag_mod.Asset = dict
    rag_mod.IngestResponse = dict
    rag_mod.RetrieveResponse = dict
    rag_mod.RetrievedChunk = dict
    sys.modules['adkpy.tools.arango_graph_rag_tool'] = rag_mod

    vision_mod = types.ModuleType('adkpy.tools.vision_contrast_tool')

    class _DummyVisionTool:
        pass

    vision_mod.VisionContrastTool = _DummyVisionTool
    vision_mod.VisionAnalyzeInput = dict
    vision_mod.VisionAnalyzeOutput = dict
    sys.modules['adkpy.tools.vision_contrast_tool'] = vision_mod

if 'workflows.tools' not in sys.modules:
    wf_tools = types.ModuleType('workflows.tools')
    wf_tools.rag_ingest_workflow_tool = lambda **kwargs: {"ingested": True}
    wf_tools.rag_retrieve_workflow_tool = lambda **kwargs: {"chunks": []}
    wf_tools.finalize_payload = lambda **kwargs: {"slides": kwargs.get("slides", [])}
    wf_tools.evaluate_quality = lambda **kwargs: {"should_continue": False}
    wf_tools.map_theme_to_design = lambda **kwargs: {"background": "brand-gradient-soft", "pattern": "grid"}
    wf_tools.prepare_design_payload = lambda **kwargs: {"design": {kwargs.get("slideId"): {"tokens": kwargs.get("tokens")}}}
    wf_tools.prepare_critic_payload = lambda **kwargs: {"slides": [kwargs.get("critique", {})]}
    wf_tools.prepare_notes_payload = lambda **kwargs: {"notes": {kwargs.get("slideId"): "notes"}}
    wf_tools.select_notes_tone = lambda **kwargs: {"tone": "professional"}
    wf_tools.load_slides_from_input = lambda **kwargs: {"slides": kwargs.get("slides", [])}
    wf_tools.collect_regression_metrics = lambda **kwargs: {"metrics": {}}
    wf_tools.prepare_research_summary = lambda **kwargs: {"research": {"findings": []}}
    wf_tools.WORKFLOW_TOOLS = []
    sys.modules['workflows.tools'] = wf_tools

# Stub google.adk dependency for tests
if 'google.adk.tools.function_tool' not in sys.modules:
    google_mod = types.ModuleType('google')
    adk_mod = types.ModuleType('google.adk')
    tools_mod = types.ModuleType('google.adk.tools')
    function_tool_mod = types.ModuleType('google.adk.tools.function_tool')

    class _DummyFunctionTool:
        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name', 'dummy')
            self.description = kwargs.get('description', '')
            self.func = kwargs.get('func')

    function_tool_mod.FunctionTool = _DummyFunctionTool
    tools_mod.function_tool = function_tool_mod
    adk_mod.tools = tools_mod
    google_mod.adk = adk_mod
    sys.modules['google'] = google_mod
    sys.modules['google.adk'] = adk_mod
    sys.modules['google.adk.tools'] = tools_mod
    sys.modules['google.adk.tools.function_tool'] = function_tool_mod


import pytest
from fastapi import FastAPI

pytestmark = pytest.mark.anyio("asyncio")

from adkpy.app.workflow_runner import WorkflowRunner


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_workflow_runner_session_resume():
    app = FastAPI()

    session_id = "sess-123"
    clarify_calls = {"count": 0}

    @app.post("/v1/clarify")
    async def clarify(payload: dict):  # type: ignore[unused-ignore]
        clarify_calls["count"] += 1
        history = payload.get("history") or []
        if len(history) < 2:
            return {
                "finished": False,
                "refinedGoals": "Need more context",
                "session_id": session_id,
            }
        return {
            "finished": True,
            "refinedGoals": "Pitch the Q4 roadmap",
            "session_id": session_id,
        }

    @app.post("/v1/outline")
    async def outline(payload: dict):  # type: ignore[unused-ignore]
        return {"outline": ["Slide 1"]}

    @app.post("/v1/slide/write")
    async def write(payload: dict):  # type: ignore[unused-ignore]
        return {
            "slides": [
                {
                    "id": "slide-1",
                    "title": "Slide 1",
                    "content": ["Key point"],
                    "speakerNotes": "Notes",
                    "imagePrompt": "background",
                }
            ]
        }

    runner = WorkflowRunner()
    base_spec = runner._load_spec("presentation_workflow")
    runner.specs["presentation_workflow"] = {"steps": [s for s in base_spec.get("steps", []) if s.get("id") in {"clarify", "outline", "slide_generation"}]}
    runner._TOOL_MAP = {
        "graph_rag.ingest": lambda **_: {"ingested": True},
        "graph_rag.retrieve": lambda **_: {"chunks": []},
        "workflow.finalize_payload": lambda **kwargs: {"slides": kwargs.get("slides", [])},
        "workflow.evaluate_quality": lambda **_: {"should_continue": False},
        "workflow.map_design_tokens": lambda **kwargs: {"background": "brand-gradient-soft", "pattern": "grid"},
        "workflow.prepare_design_payload": lambda **kwargs: {"design": {kwargs.get("slideId"): {"tokens": kwargs.get("tokens")}}},
        "workflow.prepare_critic_payload": lambda **kwargs: {"slides": [kwargs.get("critique", {})]},
        "workflow.prepare_notes_payload": lambda **kwargs: {"notes": {kwargs.get("slideId"): "notes"}},
        "workflow.select_notes_tone": lambda **kwargs: {"tone": "professional"},
        "workflow.load_slides": lambda **kwargs: {"slides": kwargs.get("slides", [])},
        "workflow.collect_regression_metrics": lambda **kwargs: {"metrics": {}},
        "workflow.prepare_research_summary": lambda **kwargs: {"research": {"findings": []}},
    }

    base_inputs = {
        "presentationId": "demo-1",
        "history": [{"role": "user", "content": "Build a Q4 roadmap story."}],
        "initialInput": {
            "text": "Pitch Q4 roadmap",
            "audience": "executive",
            "length": "medium",
        },
        "newFiles": [],
    }

    first = await runner.run(app, base_inputs)
    assert first["final"]["status"] == "needs_clarification"
    first_session = first["sessionId"]
    assert first_session
    assert clarify_calls["count"] == 1

    resumed_payload = {
        **base_inputs,
        "sessionId": first_session,
        "state": first["state"],
        "history": base_inputs["history"]
        + [{"role": "user", "content": "Audience cares about LTV."}],
    }

    second = await runner.run(app, resumed_payload)
    assert second["sessionId"] == first_session
    assert second["state"]["slides"], "expected slides after resume"
    assert second["trace"], "combined trace should be returned"
    assert len(second["trace"]) > len(first["trace"]), "resume should add new steps"
    assert clarify_calls["count"] == 2
