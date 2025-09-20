from adkpy.workflows.tools import (
    prepare_critic_payload,
    prepare_notes_payload,
    select_notes_tone,
    load_slides_from_input,
    collect_regression_metrics,
    prepare_research_summary,
)


def test_prepare_critic_payload_injects_slide_id():
    result = prepare_critic_payload("slide-42", {"title": "Refined", "content": ["Point"]})
    assert result["slides"][0]["id"] == "slide-42"
    assert result["slides"][0]["title"] == "Refined"


def test_prepare_notes_payload_reads_rephrased_field():
    result = prepare_notes_payload("slide-1", {"rephrasedSpeakerNotes": "Tight notes"})
    assert result == {"notes": {"slide-1": "Tight notes"}}


def test_prepare_notes_payload_handles_missing():
    result = prepare_notes_payload("slide-1", None)
    assert result == {"notes": {}}

from adkpy.workflows.tools import select_notes_tone


def test_select_notes_tone_handles_dict():
    tone = select_notes_tone({"tone": {"style": "conversational"}})
    assert tone == {"tone": "conversational"}


def test_select_notes_tone_defaults():
    tone = select_notes_tone({})
    assert tone == {"tone": "professional"}

from types import SimpleNamespace


def test_load_slides_from_input_normalises():
    data = load_slides_from_input([{"id": "slide-1", "title": "Title"}])
    assert data == {"slides": [{"id": "slide-1", "title": "Title"}]}


def test_collect_regression_metrics_counts_tokens():
    slide = SimpleNamespace(content=["a", "b"], design={"tokens": {"background": "token"}})
    state = SimpleNamespace(slides=[slide], script="", rag={})
    regression = collect_regression_metrics(state)
    metrics = regression["metrics"]
    assert metrics["slideCount"] == 1
    assert metrics["designTokenCount"] == 1
    assert len(regression["slides"]) == 1


def test_prepare_research_summary_handles_missing():
    summary = prepare_research_summary({"research": {"findings": ["Fact"]}})
    assert summary == {"research": {"findings": ["Fact"]}}
