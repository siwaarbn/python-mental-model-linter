"""
feedback
========

The feedback generator.

Maps a Finding (produced by registry.py) to a four-layer feedback card:
  Layer 1 — Observation:              what the analysis engine noticed
  Layer 2 — Conceptual Explanation:    the misconception, explained
  Layer 3 — Mental Model Correction:   the correct way to think about it
  Layer 4 — Reflection Prompt:         a question, not an answer

Progressive disclosure: a UI can show Layer 1 first and let the student
choose to expand Layers 2-4, rather than dumping everything at once.
"""
