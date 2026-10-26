"""
False-positive sweep: for each of the 22 rules, run one or more pieces of
CORRECT/idiomatic Python through the real pipeline and report any finding
that fires anyway. Not a replacement for the existing 74 unit tests --
those already check "rule fires on bad code" and a few "doesn't fire on
obviously safe code" cases per rule. This script specifically hunts for
plausible real-world code that LOOKS like the misconception pattern but
isn't one, guided by the "False Positive Risk" notes already documented
in the rule docstrings plus structural reading of each rule's check().
"""
from analysis_engine.pipeline import analyze

# Each entry: (rule_id_expected_clean, description, source_code)
CASES = [
    ("R-M1-01", "legit: last-value tracking used as scalar afterward, not a collection",
     "best = 0\nfor score in [3, 9, 1]:\n    best = score\nprint(best)\n"),

    ("R-M1-02", "legit: list rebuilt on purpose each iteration and used inside the loop",
     "row = []\nfor i in range(3):\n    row = [i, i * 2]\n    print(row)\n"),

    ("R-M2-01", "legit: intentional shared reference (aliasing on purpose)",
     "log = []\nrecent = log\nrecent.append('start')\nprint(log)\n"),

    ("R-M3-01", "legit: 'is None' check",
     "x = None\nif x is None:\n    print('empty')\n"),

    ("R-M3-02", "legit: plain boolean condition, no explicit compare",
     "flag = True\nif flag:\n    print('on')\n"),

    ("R-M4-01", "legit: while loop condition changed via mutation, not reassignment",
     "queue = [1, 2, 3]\nwhile queue:\n    item = queue.pop()\n    print(item)\n"),

    ("R-M4-02", "legit: range(n) used correctly, no n-th index access",
     "items = [10, 20, 30]\nfor i in range(len(items)):\n    print(items[i])\n"),

    ("R-M5-01", "legit: find-first-match idiom, implicit None fallthrough",
     "def find_first_negative(nums):\n    for n in nums:\n        if n < 0:\n            return n\n"),

    ("R-M5-02", "legit: function has a return, also prints for debugging",
     "def compute(x):\n    print('computing', x)\n    return x * 2\n\nresult = compute(3)\n"),

    ("R-M5-03", "legit: return inside if/else, no code after either branch",
     "def sign(x):\n    if x < 0:\n        return -1\n    else:\n        return 1\n"),

    ("R-M6-01", "legit: module-level variable read after being set at module scope",
     "counter = 0\ndef bump():\n    global counter\n    counter += 1\nbump()\nprint(counter)\n"),

    ("R-M6-02", "legit: global declared before use inside function",
     "total = 0\ndef add(n):\n    global total\n    total += n\nadd(5)\n"),

    ("R-M6-03", "legit: parameter shares a global's name but is called with varying arguments",
     "limit = 10\ndef capped(limit):\n    return min(limit, 10)\ncapped(3)\ncapped(7)\n"),

    ("R-M7-01", "legit: accumulator initialised before loop",
     "total = 0\nfor n in [1, 2, 3]:\n    total += n\nprint(total)\n"),

    ("R-M7-02", "legit: printing running total inside loop for progress/debugging",
     "total = 0\nfor n in [1, 2, 3]:\n    total += n\n    print(total)\nprint(total)\n"),

    ("R-M8-01", "legit: capturing pop()'s return value (excluded mutator)",
     "items = [1, 2, 3]\nlast = items.pop()\nprint(last)\n"),

    ("R-M8-02", "legit: user-defined fluent .add() that returns self, used as a call argument",
     "class Cart:\n    def __init__(self):\n        self.items = []\n    def add(self, item):\n        self.items.append(item)\n        return self\n\ndef describe(cart):\n    return str(cart.items)\n\nc = Cart()\nprint(describe(c.add('apple')))\n"),

    ("R-M9-01", "legit: attribute access used as part of an expression, not a bare statement",
     "class Box:\n    def __init__(self):\n        self.value = 1\nb = Box()\nprint(b.value)\n"),

    ("R-M9-02", "legit: function name also used as a variable elsewhere (ambiguous, suppressed)",
     "def process():\n    pass\nprocess = None\nprocess\n"),

    ("R-M10-01", "legit: deliberately parenthesized and/or mix",
     "a, b, c = True, False, True\nif (a and b) or c:\n    print('ok')\n"),

    ("R-M11-01", "legit: container reassigned to None as a sentinel before the None-check",
     "cache = []\ncache = None\nif cache is None:\n    print('not ready')\n"),

    ("R-M11-02", "legit: modulo used for parity check (explicitly excluded op)",
     "n = 4\nif n % 2:\n    print('odd')\n"),
]


def main():
    total = len(CASES)
    flagged = []
    for rule_id, description, source in CASES:
        result = analyze(source)
        if not result.success:
            print(f"[PARSE ERROR] {rule_id}: {description}\n  {result.parse_error}")
            continue
        hit_ids = [c.rule_id for c in result.feedback_cards]
        if rule_id in hit_ids:
            flagged.append((rule_id, description, source))
            print(f"[FALSE POSITIVE] {rule_id}: {description}")
            for c in result.feedback_cards:
                if c.rule_id == rule_id:
                    print(f"    -> {c.layer1_observation}")
        else:
            print(f"[clean]           {rule_id}: {description}")

    print(f"\n{len(flagged)}/{total} cases produced an unwanted finding on correct code.")


if __name__ == "__main__":
    main()
