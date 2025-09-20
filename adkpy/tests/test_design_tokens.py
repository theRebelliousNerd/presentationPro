from adkpy.config.settings import load_design_tokens
from adkpy.agents.design.tools.backgrounds import build_background_code
from adkpy.workflows.tools import map_theme_to_design, prepare_design_payload


def test_design_tokens_schema_contains_expected_sections():
    tokens = load_design_tokens()
    assert "colors" in tokens
    assert "backgrounds" in tokens
    assert "patterns" in tokens


def test_build_background_code_returns_token_metadata():
    tokens = load_design_tokens()
    payload = build_background_code("brand", "grid")
    assert payload["tokens"]["background"] in tokens["backgrounds"]
    assert payload["css"]
    assert payload["tokens"]["pattern"] in tokens["patterns"]


def test_map_theme_to_design_falls_back_to_tokens():
    selection = map_theme_to_design({"graphicStyle": "modern"}, {"metadata": {}})
    tokens = load_design_tokens()
    assert selection["background"].startswith("brand-")
    assert selection["pattern"] in tokens["patterns"]
    assert selection["overlay"] in tokens.get("overlays", {})
    assert selection["layout"] in tokens.get("layouts", {})


def test_prepare_design_payload_wraps_agent_response():
    design_payload = prepare_design_payload(
        "slide-1",
        {"type": "code", "code": {"css": "body {}"}},
        {"background": "brand-gradient-soft", "pattern": "grid"},
        presentationId="demo",
    )
    assert "design" in design_payload
    assert "slide-1" in design_payload["design"]
    entry = design_payload["design"]["slide-1"]
    assert entry["tokens"]["pattern"] == "grid"
    assert entry["code"]["css"] == "body {}"
