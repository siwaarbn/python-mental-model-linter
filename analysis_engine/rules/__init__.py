"""
rules
=====

Independent, pluggable rule matchers (Strategy pattern). Each module
here groups the rule(s) for one misconception (M1, M2, ...). See
rules/base.py for the shared Rule/Finding interface, and
registry.py for how these get run against a SubmissionContext.
"""
