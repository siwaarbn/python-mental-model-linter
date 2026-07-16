from analysis_engine.rules.base import Finding
from analysis_engine.feedback.generator import FeedbackGenerator
from analysis_engine.feedback.templates import get_template


def test_generate_produces_all_four_layers():
    finding = Finding(
        rule_id="R-M1-02", misconception_id="M1", line=3, column=4,
        message="observed thing", confidence="HIGH",
    )
    card = FeedbackGenerator().generate(finding)
    assert card.layer1_observation == "observed thing"
    assert card.misconception_name == "Variable Persistence Misconception"
    assert card.severity == 2
    assert card.layer2_conceptual_explanation
    assert card.layer3_mental_model_correction
    assert card.layer4_reflection_prompt


def test_unknown_misconception_id_falls_back_to_pending_template():
    template = get_template("M999")
    assert template.name == "(misconception content pending)"


def test_generate_all_preserves_order():
    findings = [
        Finding(rule_id="R-M3-01", misconception_id="M3", line=1, column=0,
                message="a", confidence="HIGH"),
        Finding(rule_id="R-M4-01", misconception_id="M4", line=2, column=0,
                message="b", confidence="HIGH"),
    ]
    cards = FeedbackGenerator().generate_all(findings)
    assert [c.rule_id for c in cards] == ["R-M3-01", "R-M4-01"]
