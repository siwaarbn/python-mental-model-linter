"""
Thin wrapper around analysis_engine.pipeline.analyze().

Turns the pipeline's result into the plain structure the API returns.
"""
from analysis_engine.pipeline import analyze


def _format_parse_error(error) -> str:
    """
    Turns a parser.ParseError (message, line, column, bad_line_text) into
    the single display string the API and frontend expect.
    """
    location = f" (line {error.line}" + (f", col {error.column}" if error.column is not None else "") + ")"
    text = f"{error.message}{location if error.line is not None else ''}"
    if error.bad_line_text:
        text += f"\n    {error.bad_line_text.strip()}"
    return text


def run_analysis(source_code: str) -> dict:
    """
    Returns {"parse_error": str | None, "findings": [FeedbackCard, ...]}.
    """
    result = analyze(source_code)

    if not result.success:
        return {"parse_error": _format_parse_error(result.parse_error), "findings": []}

    return {"parse_error": None, "findings": result.feedback_cards}
