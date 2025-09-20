from adkpy.agents.clarifier.tools.analysis import (
    analyze_context,
    generate_question,
    summarize_goals,
)


def test_analyze_context_uses_structured_form_data():
    initial_input = {
        "text": "Create a quarterly analytics update deck",
        "audience": "Product VPs and Directors",
        "objective": "Secure roadmap approval",
        "length": "20 minutes",
        "tone": {"formality": 3, "energy": 2},
        "keyMessages": ["Highlight adoption", "Show impact metrics"],
        "successCriteria": ["Leadership signs off"],
        "designLayoutToken": "two-column",
        "designOverlayToken": "beige-ribbon",
    }

    result = analyze_context(history=[], initial_input=initial_input)

    assert result["has_audience"] is True
    assert result["has_objective"] is True
    assert result["has_layout"] is True
    assert result["has_overlay"] is True
    assert result["needs_more_info"] is False
    assert result["understanding_level"] >= 0.7


def test_generate_question_targets_missing_field_first():
    context = {
        "missing_fields": ["objective", "duration"],
        "needs_more_info": True,
    }
    history = [
        {"role": "assistant", "content": "Who is the audience?"},
        {"role": "user", "content": "Enterprise customers in healthcare."},
    ]

    question = generate_question(context, history)

    assert "objective" in question.lower() or "primary" in question.lower()


def test_summarize_goals_merges_form_and_history():
    initial_input = {
        "text": "Pitch VisionCV design intelligence",
        "audience": "Product stakeholders evaluating our roadmap",
        "objective": "Demonstrate how VisionCV accelerates analysis",
        "keyMessages": ["Explain workflow", "Highlight case study"],
    }
    history = [
        {"role": "assistant", "content": "Is there a call to action?"},
        {"role": "user", "content": "Yes, ask them to approve a pilot rollout."},
    ]

    summary = summarize_goals(history, initial_input)

    assert "VisionCV design intelligence" in summary
    assert "Product stakeholders" in summary
    assert "pilot rollout" in summary
