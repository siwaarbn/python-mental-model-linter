"""
pipeline.py
===========

The single function a caller (API layer, CLI, or a test) actually
needs: give it source code, get back either a parse error or a list of
FeedbackCards. Wires together every Month 2 component in order:

    parse_source -> build_context -> run_all_rules -> FeedbackGenerator
"""

from dataclasses import dataclass
from typing import Optional

from analysis_engine.parser import parse_source, ParseError
from analysis_engine.context_builder import build_context
from analysis_engine.registry import run_all_rules
from analysis_engine.feedback.generator import FeedbackGenerator


@dataclass
class AnalysisResult:
    success: bool
    parse_error: Optional[ParseError]
    feedback_cards: list  # list[FeedbackCard], empty if parsing failed


def analyze(code: str, filename: str = "<student_submission>") -> AnalysisResult:
    parse_result = parse_source(code, filename=filename)
    if not parse_result.success:
        return AnalysisResult(success=False, parse_error=parse_result.error, feedback_cards=[])

    context = build_context(parse_result.tree, source=code)
    findings = run_all_rules(context)
    cards = FeedbackGenerator().generate_all(findings)
    return AnalysisResult(success=True, parse_error=None, feedback_cards=cards)
