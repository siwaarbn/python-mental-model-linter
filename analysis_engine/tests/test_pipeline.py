from analysis_engine.pipeline import analyze


def test_pipeline_reports_parse_error_gracefully():
    result = analyze("if x == 1\n    print('hi')\n")
    assert result.success is False
    assert result.parse_error is not None
    assert result.feedback_cards == []


def test_pipeline_end_to_end_produces_feedback_cards():
    src = (
        "flag = True\n"
        "if flag == True:\n"
        "    print('yes')\n"
    )
    result = analyze(src)
    assert result.success is True
    assert len(result.feedback_cards) == 1
    card = result.feedback_cards[0]
    assert card.rule_id == "R-M3-02"
    assert card.layer1_observation
    assert card.layer4_reflection_prompt


def test_pipeline_clean_code_produces_no_findings():
    src = "def add(a, b):\n    return a + b\nprint(add(2, 3))\n"
    result = analyze(src)
    assert result.success is True
    assert result.feedback_cards == []
