import sys
import types

# Stub google.generativeai for tests so wrappers import without the SDK
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


from adkpy.agents.wrappers import SlideWriterAgent, SlideWriterInput


def test_slide_writer_adds_rag_sources(monkeypatch):
    agent = SlideWriterAgent()

    def fake_llm(prompt_parts):  # type: ignore[unused-argument]
        response = '{"title": "Slide 1", "content": ["A"], "speakerNotes": "Note", "imagePrompt": "Prompt"}'
        usage = {"model": "test", "promptTokens": 5, "completionTokens": 9, "durationMs": 0}
        return response, usage

    monkeypatch.setattr(agent, "llm", fake_llm)

    rag_context = {
        "presentation": [
            {"text": "General fact about revenue", "name": "Overview", "url": "https://example.com/overview"}
        ],
        "sections": {
            "Slide 1": {
                "title": "Slide 1",
                "chunks": [
                    {"text": "Specific KPI lifted 25%", "name": "Q4 report", "url": "https://example.com/report"}
                ],
            }
        },
    }

    data = SlideWriterInput(
        outline=["Slide 1"],
        clarifiedContent="Focus on KPI improvements",
        ragContext=rag_context,
    )

    result = agent.run(data)
    slide = result.data[0]
    assert slide["metadata"]["ragSources"], "expected ragSources metadata"
    assert any("Q4 report" in citation for citation in slide.get("citations", []))
