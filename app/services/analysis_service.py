"""
Thin wrapper around analysis_engine.pipeline.analyze().

>>> DROP YOUR REAL analysis_engine/ FOLDER INTO backend/analysis_engine/ <<<

This module intentionally does nothing clever: it imports your Month 2
pipeline and calls analyze(source_code) exactly the way you already
designed it to be called. If that import succeeds, everything below it
is just glue -- turning ParseResult / FeedbackCard objects into the
Pydantic schemas the API already speaks.

A fallback stub is included ONLY so the API is runnable and testable
before you've copied your real engine in. It is obviously fake (it
always returns one hardcoded finding) so it can never be mistaken for
real detection output. Delete FakePipeline once your real
analysis_engine/ is in place -- or just leave it; it's only used when
the real import fails.
"""
from dataclasses import dataclass
from typing import Optional

try:
    from analysis_engine.pipeline import analyze as _real_analyze
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False


@dataclass
class _StubFeedbackCard:
    rule_id: str
    misconception_id: str
    misconception_name: str
    severity: int
    line: Optional[int]
    column: Optional[int]
    confidence: Optional[str]
    layer1_observation: str
    layer2_conceptual_explanation: str
    layer3_mental_model_correction: str
    layer4_reflection_prompt: str


def _fake_analyze(source_code: str):
    """
    Placeholder used only when backend/analysis_engine/ has not been
    populated yet. Always "detects" one illustrative finding so the
    frontend has something real to render during setup. This must
    never be presented as real detection output.
    """
    if not source_code.strip():
        return {"parse_error": None, "findings": []}

    return {
        "parse_error": None,
        "findings": [
            _StubFeedbackCard(
                rule_id="R-STUB-00",
                misconception_id="M0",
                misconception_name="(stub) analysis_engine not connected yet",
                severity=1,
                line=1,
                column=0,
                confidence="n/a",
                layer1_observation=(
                    "This is placeholder output. Drop your real analysis_engine/ "
                    "folder into backend/analysis_engine/ to see real detection results."
                ),
                layer2_conceptual_explanation="See backend/README.md for setup steps.",
                layer3_mental_model_correction="N/A -- stub response.",
                layer4_reflection_prompt="N/A -- stub response.",
            )
        ],
    }


def _format_parse_error(error) -> str:
    """
    Turns a parser.ParseError dataclass (message, line, column,
    bad_line_text) into the single display string the API/frontend
    expect. Kept separate so this is the one place that knows about
    ParseError's exact shape.
    """
    location = f" (line {error.line}" + (f", col {error.column}" if error.column is not None else "") + ")"
    text = f"{error.message}{location if error.line is not None else ''}"
    if error.bad_line_text:
        text += f"\n    {error.bad_line_text.strip()}"
    return text


def run_analysis(source_code: str) -> dict:
    """
    Returns a plain dict: {"parse_error": str | None, "findings": [FeedbackCard, ...]}

    Matches pipeline.analyze()'s real AnalysisResult exactly:
        AnalysisResult(success: bool, parse_error: Optional[ParseError], feedback_cards: list)
    """
    if not ENGINE_AVAILABLE:
        return _fake_analyze(source_code)

    result = _real_analyze(source_code)

    if not result.success:
        return {"parse_error": _format_parse_error(result.parse_error), "findings": []}

    return {"parse_error": None, "findings": result.feedback_cards}
