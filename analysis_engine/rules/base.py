"""
rules/base.py
=============

Every rule matcher (R-M1-01, R-M3-02, ...) implements the same tiny
interface: given the shared SubmissionContext, return zero or more
Finding objects. This is what makes rules independently pluggable —
registry.py doesn't know or care how a rule works internally, only
that it has a rule_id/misconception_id and a check() method.

Adding a new rule never requires touching context_builder.py, other
rules, or registry.py — only adding a new Rule subclass and, in
registry.py, appending it to ALL_RULES. This is the concrete payoff of
the Option C architecture decision from the Month 2 design.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from analysis_engine.context_builder import SubmissionContext


@dataclass
class Finding:
    """
    One rule firing on one piece of code. This is the unit of output
    that flows from the Rule Engine into the Feedback Generator.
    """
    rule_id: str                # e.g. "R-M1-02"
    misconception_id: str       # e.g. "M1"
    line: Optional[int]
    column: Optional[int]
    message: str                # short, factual observation (Layer 1 raw material)
    confidence: str             # "HIGH" | "MEDIUM" | "LOW"
    evidence: Optional[str] = None  # optional extra detail (e.g. the variable name)


class Rule(ABC):
    """Base class every detection rule matcher inherits from."""

    rule_id: str
    misconception_id: str
    confidence: str

    @abstractmethod
    def check(self, context: SubmissionContext) -> list:
        """Return a list[Finding]. Must never raise on well-formed input."""
        raise NotImplementedError

    def _finding(self, node, message: str, evidence: Optional[str] = None) -> Finding:
        return Finding(
            rule_id=self.rule_id,
            misconception_id=self.misconception_id,
            line=getattr(node, "lineno", None),
            column=getattr(node, "col_offset", None),
            message=message,
            confidence=self.confidence,
            evidence=evidence,
        )
