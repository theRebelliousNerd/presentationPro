"""Regression harness for workflow evaluation datasets."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

EVALS_DIR = Path(__file__).parent / "evals"


def _load_eval(name: str) -> dict:
    with (EVALS_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_clarify_outline_critic_eval_structure():
    payload = _load_eval("clarify_outline_critic.json")
    assert payload["name"] == "clarify_outline_critic_rag_smoke"
    inputs = payload["inputs"]
    assert "presentationId" in inputs
    assert inputs["newFiles"], "expected at least one seeded asset"
    assertions = payload["assertions"]
    assert assertions["clarify"]["expects_finished"] is True
    assert assertions["critic"]["max_missing_citations"] == 0


@pytest.mark.parametrize("dataset", sorted(p.name for p in EVALS_DIR.glob("*.json")))
def test_eval_datasets_are_ascii(dataset: str):
    data = (EVALS_DIR / dataset).read_text(encoding="utf-8")
    for char in data:
        assert ord(char) < 128, f"Non-ASCII character {repr(char)} found in {dataset}"
