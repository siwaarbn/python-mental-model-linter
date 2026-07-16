"""
registry.py
===========

Component 3 of the Month 2 pipeline: the Rule Engine.

This is deliberately thin. It knows nothing about how any individual
rule detects a misconception — it just holds the list of every
registered Rule instance, runs each one's check() against the shared
SubmissionContext built by context_builder.py, and collects the
Finding objects they return. This is the "independent pluggable rule
matchers" half of the Option C architecture; context_builder.py is the
"single-pass context builder" half.

All 22 rules from the finalized Month 1 taxonomy are active.
"""

from analysis_engine.context_builder import SubmissionContext
from analysis_engine.rules.m1_rules import (
    RM1_01_LoopBodyOverwrite,
    RM1_02_ListAccumulationWithoutAppend,
)
from analysis_engine.rules.m2_rules import RM2_01_MutableAliasWithoutCopy
from analysis_engine.rules.m3_rules import (
    RM3_01_IdentityComparisonToLiteral,
    RM3_02_ExplicitBooleanComparison,
)
from analysis_engine.rules.m4_rules import (
    RM4_01_StaticWhileCondition,
    RM4_02_OffByOneInRange,
)
from analysis_engine.rules.m5_rules import (
    RM5_01_ReturnInsideAccumulationLoop,
    RM5_02_PrintUsedAsFunctionReturn,
    RM5_03_UnreachableCodeAfterReturn,
)
from analysis_engine.rules.m6_rules import (
    RM6_01_OutOfScopeVariableRead,
    RM6_02_ShadowGlobalWithoutDeclaration,
    RM6_03_UnnecessaryGlobalReparameterisation,
)
from analysis_engine.rules.m7_rules import (
    RM7_01_MissingAccumulatorInitialisation,
    RM7_02_PrematureAccumulatorRead,
)
from analysis_engine.rules.m8_rules import (
    RM8_01_ReassignmentOfNoneReturningMutatorCall,
    RM8_02_MutatorCallAsValueProducingSubExpression,
)
from analysis_engine.rules.m9_rules import (
    RM9_01_BareAttributeAccessAsStatement,
    RM9_02_BareNameReferenceAsStatement,
)
from analysis_engine.rules.m10_rules import RM10_01_UnparenthesizedMixedBooleanOperators
from analysis_engine.rules.m11_rules import (
    RM11_01_ContainerComparedToNoneForEmptiness,
    RM11_02_BareArithmeticAsCondition,
)

# All 22 rules from the finalized Month 1 taxonomy, registered by ID.
ALL_RULES = [
    RM1_01_LoopBodyOverwrite(),
    RM1_02_ListAccumulationWithoutAppend(),
    RM2_01_MutableAliasWithoutCopy(),
    RM3_01_IdentityComparisonToLiteral(),
    RM3_02_ExplicitBooleanComparison(),
    RM4_01_StaticWhileCondition(),
    RM4_02_OffByOneInRange(),
    RM5_01_ReturnInsideAccumulationLoop(),
    RM5_02_PrintUsedAsFunctionReturn(),
    RM5_03_UnreachableCodeAfterReturn(),
    RM6_01_OutOfScopeVariableRead(),
    RM6_02_ShadowGlobalWithoutDeclaration(),
    RM6_03_UnnecessaryGlobalReparameterisation(),
    RM7_01_MissingAccumulatorInitialisation(),
    RM7_02_PrematureAccumulatorRead(),
    RM8_01_ReassignmentOfNoneReturningMutatorCall(),
    RM8_02_MutatorCallAsValueProducingSubExpression(),
    RM9_01_BareAttributeAccessAsStatement(),
    RM9_02_BareNameReferenceAsStatement(),
    RM10_01_UnparenthesizedMixedBooleanOperators(),
    RM11_01_ContainerComparedToNoneForEmptiness(),
    RM11_02_BareArithmeticAsCondition(),
]


def run_all_rules(context: SubmissionContext, rules=None) -> list:
    """
    Run every registered rule (or a caller-supplied subset) against the
    context and return a flat, source-order-sorted list of Findings.
    A single misbehaving rule cannot take down the whole scan — its
    exception is caught and swallowed with the rule's ID attached, so
    one bad rule degrades gracefully instead of crashing the pipeline.
    """
    rules_to_run = rules if rules is not None else ALL_RULES
    findings = []
    for rule in rules_to_run:
        try:
            findings.extend(rule.check(context))
        except Exception as exc:  # noqa: BLE001 - intentional: isolate rule failures
            findings.append(_engine_error_finding(rule, exc))

    findings.sort(key=lambda f: (f.line if f.line is not None else 0, f.rule_id))
    return findings


def _engine_error_finding(rule, exc: Exception):
    from analysis_engine.rules.base import Finding
    return Finding(
        rule_id=rule.rule_id,
        misconception_id=rule.misconception_id,
        line=None,
        column=None,
        message=f"Rule engine error while running {rule.rule_id}: {exc}",
        confidence="ENGINE_ERROR",
    )


def rule_coverage_report() -> dict:
    """{rule_id: misconception_id} for every registered rule."""
    return {rule.rule_id: rule.misconception_id for rule in ALL_RULES}
