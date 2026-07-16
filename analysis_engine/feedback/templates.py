"""
templates.py
============

The feedback template library. One entry per misconception (M1-M11),
matching the finalized Month 1 taxonomy. Each template supplies
severity and Layers 2-4 (Layer 1 always comes from the Finding's own
`message`, since that's specific to what was actually found in THIS
submission — Layers 2-4 are the same for every student who trips the
same misconception).

Severity (1-3) is the taxonomy's resistance-to-correction scale:
  1 = missing knowledge (a single clear demonstration usually fixes it)
  2 = a wrong belief that needs replacing (resists a single correction)
  3 = a threshold concept (requires reconstructing the mental model)
"""

from dataclasses import dataclass


@dataclass
class MisconceptionTemplate:
    name: str
    severity: int
    conceptual_explanation: str      # Layer 2
    mental_model_correction: str     # Layer 3
    reflection_prompt: str           # Layer 4


TEMPLATES = {
    "M1": MisconceptionTemplate(
        name="Variable Persistence Misconception",
        severity=2,
        conceptual_explanation=(
            "It's easy to assume a variable is a running record — that it "
            "remembers every value it has ever held, not just the current "
            "one. In Python, a variable holds exactly one value at any "
            "time: the most recently assigned value. Previous values are "
            "gone unless you explicitly stored them somewhere else."
        ),
        mental_model_correction=(
            "Think of a variable as a single labeled box, not a growing "
            "shelf. '=' takes whatever is currently in the box, throws it "
            "away, and puts the new thing in. If you want a shelf that "
            "grows, you need an actual list, and you add to it explicitly "
            "with .append(...)."
        ),
        reflection_prompt=(
            "If you ran this loop by hand and wrote down the value of the "
            "variable after every single iteration, how many different "
            "values would you write down — and which one is left at the end?"
        ),
    ),
    "M2": MisconceptionTemplate(
        name="Assignment Direction Misconception",
        severity=2,
        conceptual_explanation=(
            "'b = a' looks like it should make b a fresh, independent copy "
            "of whatever a holds — that's how it works with numbers. "
            "Assignment is actually a directional, one-time copy operation: "
            "it reads the current value of a and stores it in b. But for "
            "mutable objects like lists and dictionaries, that 'value' IS "
            "the object itself — so b doesn't get a copy of the contents, "
            "it gets a second name for the exact same object."
        ),
        mental_model_correction=(
            "Picture a and b as two sticky notes with the same address "
            "written on them, both pointing at one house. Redecorating the "
            "house through the 'a' note also changes what you see when you "
            "walk to the house via the 'b' note — there's only ever one "
            "house. If you actually want two separate houses, you need to "
            "explicitly copy (e.g. b = a.copy() or b = list(a))."
        ),
        reflection_prompt=(
            "After you modified one of the two names, did you expect the "
            "other name's value to change too? Why do you think it did (or "
            "didn't) here?"
        ),
    ),
    "M3": MisconceptionTemplate(
        name="Comparison-as-Assignment / Identity-vs-Equality Misconception",
        severity=2,
        conceptual_explanation=(
            "'=' and '==' look similar but do completely different jobs: "
            "'=' is an imperative action that stores a value; '==' is a "
            "query that produces a Boolean without modifying anything. "
            "'is' is a third, different question again — it asks whether "
            "two names refer to the literal same object in memory, not "
            "whether they hold equal values. For small integers and "
            "interned strings 'is' can accidentally look like it works, "
            "which makes the misconception hard to notice."
        ),
        mental_model_correction=(
            "Ask three separate questions and use three separate tools: "
            "'do I want to store this?' -> use '=' (a statement, not an "
            "expression). 'Do these two things have equal value?' -> use "
            "'=='. 'Are these two names the exact same object?' -> use "
            "'is', and reserve it for singleton checks like 'is None'."
        ),
        reflection_prompt=(
            "What question were you actually trying to ask here — 'do "
            "these have the same value' or 'are these the same object'? "
            "Which operator asks that question?"
        ),
    ),
    "M4": MisconceptionTemplate(
        name="Loop Termination Misconception",
        severity=2,
        conceptual_explanation=(
            "A while-loop's condition is not checked once and then "
            "trusted — it is re-evaluated fresh at the start of every "
            "single iteration, and the body either runs fully or not at "
            "all for that iteration. If nothing inside the loop body "
            "changes the values the condition depends on, the condition's "
            "truth value can never flip, which either skips the loop "
            "entirely or runs it forever."
        ),
        mental_model_correction=(
            "Think of the while-condition as a bouncer checking IDs at a "
            "door, once per person let through. The bouncer doesn't "
            "remember checking last time — every single iteration, "
            "something inside the loop has to actually change what the "
            "bouncer sees, or the answer will always be the same."
        ),
        reflection_prompt=(
            "Which specific line inside the loop body is supposed to "
            "change the value(s) the while-condition depends on? Can you "
            "point to it?"
        ),
    ),
    "M5": MisconceptionTemplate(
        name="Return Semantics Misconception",
        severity=3,
        conceptual_explanation=(
            "'return' does two things at once: it hands a value back to "
            "the caller, AND it immediately terminates the function — no "
            "code after it in that call ever runs, and a return inside a "
            "loop stops the loop on that very iteration. It does not "
            "'collect' values across iterations the way append() would, "
            "and it is not the same thing as print(), which only sends "
            "text to the console without making a value available to the "
            "calling code. A function that ends without a return "
            "statement returns None."
        ),
        mental_model_correction=(
            "Think of return as handing over a single item and walking out "
            "of the room — the function call is over the instant return "
            "executes. If you want to gather multiple results, build a "
            "list across all iterations and return that ONE list after the "
            "loop finishes, not a single item from inside it."
        ),
        reflection_prompt=(
            "If this function is called once, how many times can 'return' "
            "actually execute during that one call? What does that tell "
            "you about what happens after the first matching item?"
        ),
    ),
    "M6": MisconceptionTemplate(
        name="Scope Misconception",
        severity=3,
        conceptual_explanation=(
            "Each function call creates its own isolated local scope. A "
            "variable created inside a function only exists while that "
            "function is running, and it does not automatically become "
            "visible at module level once the function returns. A local "
            "variable that happens to share a name with a global variable "
            "shadows it inside the function without affecting the global "
            "at all. The same underlying confusion can also run the "
            "opposite direction: believing a function can't see a global "
            "variable at all unless it's explicitly re-passed as a "
            "parameter — when in fact reading an outer-scope variable "
            "never needs any special declaration; only reassigning one "
            "does (via the 'global' keyword)."
        ),
        mental_model_correction=(
            "Think of each function call as its own private room: "
            "variables created in that room exist only while you're in it, "
            "and the room is torn down the moment the function returns. "
            "But the room's windows are never blacked out — you can always "
            "look out and read anything from an enclosing scope without "
            "asking permission. You only need a special declaration "
            "('global') the moment you want to change something outside "
            "the room, not just look at it."
        ),
        reflection_prompt=(
            "Where was this variable actually created — inside a function, "
            "or directly in the main body of the script? Does the code "
            "need to change it, or only read it — and does that change "
            "which tool (return, global, or nothing at all) is needed?"
        ),
    ),
    "M7": MisconceptionTemplate(
        name="Accumulation Pattern Misconception",
        severity=1,
        conceptual_explanation=(
            "Building a result from a sequence of computations doesn't "
            "happen automatically just by repeating the computation — "
            "Python needs an explicit accumulator variable that is "
            "initialised before the loop starts and updated (not "
            "overwritten) on every iteration, then read only after the "
            "loop finishes."
        ),
        mental_model_correction=(
            "An accumulator is like a running tally you keep on a notepad "
            "before you start counting: you write '0' first, then update "
            "that same number after each item, and you only read the "
            "final tally once counting is completely done — never mid-way "
            "through, and never skipping the initial '0'."
        ),
        reflection_prompt=(
            "Before this loop runs even once, does the accumulator "
            "variable already exist with a starting value? And inside the "
            "loop, does each step update it, or replace it?"
        ),
    ),
    "M8": MisconceptionTemplate(
        name="Mutation vs Return Value Misconception",
        severity=2,
        conceptual_explanation=(
            "Python methods fall into two distinct families that look "
            "similar in code but behave very differently. Mutating "
            "methods like .sort(), .append(), .reverse(), .extend(), and "
            ".update() change the object in place and return None — "
            "Python's own documentation confirms this design choice "
            "exists specifically to prevent this exact confusion. "
            "Non-mutating operations like the built-in sorted() or string "
            "methods like .strip() leave the original untouched and "
            "return a new object instead. You can't tell which family a "
            "method belongs to just from how it reads in English."
        ),
        mental_model_correction=(
            "Ask 'does this method change the object where it lives, or "
            "hand me back a brand-new one?' before deciding whether to "
            "capture its result. If a method mutates in place, using it "
            "is a statement on its own line — my_list.sort() — never the "
            "right side of an assignment back onto the same name."
        ),
        reflection_prompt=(
            "Does this method change the original object directly, or "
            "does it hand you back a new one? How could you check, without "
            "guessing, which one it is?"
        ),
    ),
    "M9": MisconceptionTemplate(
        name="Method Reference vs Method Call Misconception",
        severity=1,
        conceptual_explanation=(
            "A name by itself — including an attribute reached via a dot, "
            "like my_list.append — only produces a reference to that "
            "callable object. Nothing happens until that reference is "
            "followed by parentheses '()'. Writing the name alone silently "
            "evaluates to a method or function object and discards it — no "
            "error, no effect, no change to anything."
        ),
        mental_model_correction=(
            "A function or method name without '()' is like reading "
            "someone's phone number off a card without dialing it — you "
            "have the reference, but nothing happens until you actually "
            "make the call. The parentheses ARE the call."
        ),
        reflection_prompt=(
            "Did you mean to run this, or just refer to it? What would you "
            "need to add to the end of the line to actually trigger it?"
        ),
    ),
    "M10": MisconceptionTemplate(
        name="Operator Precedence Misconception",
        severity=2,
        conceptual_explanation=(
            "Logical and comparison operators are not evaluated strictly "
            "left to right the way English reads — Python applies a "
            "fixed, non-negotiable precedence table. 'not' binds tighter "
            "than 'and', which binds tighter than 'or', and comparison "
            "operators like '==' bind tighter than all three boolean "
            "operators. 'not a == b' is therefore always 'not (a == b)', "
            "never '(not a) == b' — regardless of how it might be read "
            "aloud."
        ),
        mental_model_correction=(
            "When mixing 'and', 'or', and 'not' in one expression, add "
            "parentheses around the part you mean to group, even when "
            "Python doesn't strictly require them. If you can't confidently "
            "say what the expression evaluates to for a specific input "
            "without tracing precedence rules, that's the signal to add "
            "parentheses rather than trust the reading order."
        ),
        reflection_prompt=(
            "For a specific set of input values, what do you expect this "
            "expression to evaluate to — and does adding parentheses "
            "around the part you meant to group change that answer?"
        ),
    ),
    "M11": MisconceptionTemplate(
        name="Truthiness / Boolean-Numeric Conflation Misconception",
        severity=2,
        conceptual_explanation=(
            "Every Python object has a truth value, computed implicitly "
            "whenever it appears in a boolean context like an if/while "
            "condition. 0, 0.0, None, and empty containers ([], \"\", {}) "
            "are falsy; almost everything else is truthy. 'if x:' is "
            "valid, idiomatic Python for 'if x is non-empty / non-zero / "
            "not None' — it does not require an explicit comparison. "
            "Importantly, 'empty' is not the same concept as 'is None', "
            "even though both happen to be falsy: an empty list and None "
            "are different objects entirely."
        ),
        mental_model_correction=(
            "If you can say out loud what you're checking ('is this "
            "empty?', 'are these equal?'), write that exact check "
            "explicitly: 'if not my_list:' or 'if len(my_list) == 0:' for "
            "emptiness, 'if my_list is None:' only when you actually mean "
            "'this variable was never given a list at all'. Don't rely on "
            "an arithmetic result happening to be truthy or falsy at the "
            "right moment, and don't conflate 'empty' with 'None'."
        ),
        reflection_prompt=(
            "In plain English, what condition were you trying to check "
            "here — emptiness, or that the variable was never assigned at "
            "all? Does the expression you wrote actually ask that "
            "question?"
        ),
    ),
}

_GENERIC_PENDING_TEMPLATE = MisconceptionTemplate(
    name="(misconception content pending)",
    severity=2,
    conceptual_explanation=(
        "This misconception's Layer 2-4 content has not been written yet."
    ),
    mental_model_correction="(pending)",
    reflection_prompt="(pending)",
)


def get_template(misconception_id: str) -> MisconceptionTemplate:
    return TEMPLATES.get(misconception_id, _GENERIC_PENDING_TEMPLATE)
