"""
generator.py
============

Turns a single Finding (from registry.py) into a four-layer
FeedbackCard, and offers a batch entry point for a whole submission's
worth of Findings.
"""

from dataclasses import dataclass

from analysis_engine.feedback.templates import get_template
from analysis_engine.rules.base import Finding


@dataclass
class FeedbackCard:
    rule_id: str
    misconception_id: str
    misconception_name: str
    severity: int
    line: int
    column: int
    confidence: str

    layer1_observation: str
    layer2_conceptual_explanation: str
    layer3_mental_model_correction: str
    layer4_reflection_prompt: str


class FeedbackGenerator:
    """Stateless — safe to share a single instance across a whole run."""

    def generate(self, finding: Finding) -> FeedbackCard:
        template = get_template(finding.misconception_id)
        return FeedbackCard(
            rule_id=finding.rule_id,
            misconception_id=finding.misconception_id,
            misconception_name=template.name,
            severity=template.severity,
            line=finding.line,
            column=finding.column,
            confidence=finding.confidence,
            layer1_observation=finding.message,
            layer2_conceptual_explanation=template.conceptual_explanation,
            layer3_mental_model_correction=template.mental_model_correction,
            layer4_reflection_prompt=template.reflection_prompt,
        )

    def generate_all(self, findings: list) -> list:
        return [self.generate(f) for f in findings]
