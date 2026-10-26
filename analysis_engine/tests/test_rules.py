import ast

from analysis_engine.context_builder import build_context
from analysis_engine.registry import run_all_rules, ALL_RULES, rule_coverage_report


def _findings(source: str, rule_id: str = None):
    ctx = build_context(ast.parse(source), source=source)
    all_findings = run_all_rules(ctx)
    if rule_id is None:
        return all_findings
    return [f for f in all_findings if f.rule_id == rule_id]


# ---- R-M1-01 -------------------------------------------------------------

def test_rm1_01_flags_scalar_overwrite_used_as_collection():
    src = (
        "result = 0\n"
        "for item in [1, 2, 3]:\n"
        "    result = item\n"
        "print(len(result))\n"
    )
    assert len(_findings(src, "R-M1-01")) == 1


def test_rm1_01_does_not_flag_normal_accumulator_variable():
    src = (
        "total = 0\n"
        "for item in [1, 2, 3]:\n"
        "    total = total + item\n"
        "print(len(total))\n"
    )
    assert len(_findings(src, "R-M1-01")) == 0


def test_rm1_01_does_not_flag_when_never_used_as_collection_after():
    src = "result = 0\nfor item in [1, 2, 3]:\n    result = item\nprint(result)\n"
    assert len(_findings(src, "R-M1-01")) == 0


def test_rm1_01_does_not_flag_intentional_list_reset():
    src = (
        "result = 0\n"
        "for item in [1, 2, 3]:\n"
        "    result = list()\n"
        "print(len(result))\n"
    )
    assert len(_findings(src, "R-M1-01")) == 0


# ---- R-M1-02 ---------------------------------------------------------

def test_rm1_02_flags_overwrite_of_initialised_list():
    src = "results = []\nfor item in [1, 2, 3]:\n    results = item\n"
    assert len(_findings(src, "R-M1-02")) == 1


def test_rm1_02_does_not_flag_correct_append():
    src = "results = []\nfor item in [1, 2, 3]:\n    results.append(item)\n"
    assert len(_findings(src, "R-M1-02")) == 0



def test_rm1_02_does_not_flag_list_rebuilt_and_used_only_inside_loop():
    src = "row = []\nfor i in range(3):\n    row = [i, i * 2]\n    print(row)\n"
    assert len(_findings(src, "R-M1-02")) == 0


def test_rm1_02_flags_list_rebuilt_but_read_after_loop():
    src = "items = []\nfor i in range(3):\n    items = [i]\nprint(items)\n"
    assert len(_findings(src, "R-M1-02")) == 1


# ---- R-M2-01 ---------------------------------------------------------

def test_rm2_01_flags_mutable_alias_mutated_then_original_read():
    src = "a = [1, 2, 3]\nb = a\nb.append(4)\nprint(a)\n"
    assert len(_findings(src, "R-M2-01")) == 1


def test_rm2_01_does_not_flag_when_original_not_read_after():
    src = "a = [1, 2, 3]\nb = a\nb.append(4)\nprint(b)\n"
    assert len(_findings(src, "R-M2-01")) == 0


# ---- R-M3-01 / R-M3-02 -------------------------------------------------

def test_rm3_01_flags_is_with_string_literal():
    assert len(_findings("x = 'a'\nif x is 'a':\n    pass\n", "R-M3-01")) == 1


def test_rm3_01_does_not_flag_is_none():
    assert len(_findings("x = None\nif x is None:\n    pass\n", "R-M3-01")) == 0


def test_rm3_02_flags_explicit_true_comparison():
    assert len(_findings("flag = True\nif flag == True:\n    pass\n", "R-M3-02")) == 1


def test_rm3_02_does_not_flag_plain_boolean_check():
    assert len(_findings("flag = True\nif flag:\n    pass\n", "R-M3-02")) == 0


# ---- R-M4-01 / R-M4-02 -------------------------------------------------

def test_rm4_01_flags_infinite_static_while():
    assert len(_findings("i = 0\nwhile i < 5:\n    print(i)\n", "R-M4-01")) == 1


def test_rm4_01_does_not_flag_when_body_updates_condition_var():
    assert len(_findings("i = 0\nwhile i < 5:\n    i = i + 1\n", "R-M4-01")) == 0


def test_rm4_01_does_not_flag_when_body_mutates_condition_var_via_method():
    """
    Month 4 evaluation fix: `while queue: queue.pop()` was previously a
    false positive because .pop() changes the loop's truthiness without
    ever appearing as an Assign target.
    """
    src = "queue = [1, 2, 3]\nwhile queue:\n    item = queue.pop()\n    print(item)\n"
    assert len(_findings(src, "R-M4-01")) == 0


def test_rm4_01_does_not_flag_augmented_assignment():
    """`i += 1` changes the condition variable just like `i = i + 1`."""
    assert len(_findings("i = 0\nwhile i < 5:\n    i += 1\n", "R-M4-01")) == 0


def test_rm4_01_does_not_flag_update_inside_nested_if():
    src = (
        "attempts = 0\n"
        "while attempts < 3:\n"
        "    guess = input('Guess: ')\n"
        "    if guess != 'secret':\n"
        "        attempts += 1\n"
        "    else:\n"
        "        break\n"
    )
    assert len(_findings(src, "R-M4-01")) == 0


def test_rm4_02_flags_off_by_one_index():
    src = "items = [1, 2, 3]\nfor i in range(3):\n    print(items[3])\n"
    assert len(_findings(src, "R-M4-02")) == 1


def test_rm4_02_does_not_flag_correct_indexing():
    src = "items = [1, 2, 3]\nfor i in range(3):\n    print(items[i])\n"
    assert len(_findings(src, "R-M4-02")) == 0


# ---- R-M5-01 / R-M5-02 / R-M5-03 ---------------------------------------

def test_rm5_01_flags_return_inside_loop_named_get_all():
    src = (
        "def get_all_evens(nums):\n"
        "    for n in nums:\n"
        "        if n % 2 == 0:\n"
        "            return n\n"
    )
    assert len(_findings(src, "R-M5-01")) == 1


def test_rm5_01_does_not_flag_wrapped_return_expression():
    src = "def first_even(nums):\n    for n in nums:\n        return n if n % 2 == 0 else None\n"
    assert len(_findings(src, "R-M5-01")) == 0


def test_rm5_01_does_not_flag_find_first_style_naming():
    """
    Month 4 evaluation fix: `find_first_negative` with no trailing return
    is a correct, idiomatic search-and-return-early pattern, structurally
    identical to the misconception this rule targets. Suppressed based on
    the function name signalling deliberate single-match search intent --
    mirroring how _COLLECTION_NAME_HINTS already raises confidence for the
    opposite intent.
    """
    src = "def find_first_negative(nums):\n    for n in nums:\n        if n < 0:\n            return n\n"
    assert len(_findings(src, "R-M5-01")) == 0


def test_rm5_02_flags_print_only_function_used_for_value():
    src = "def compute(x):\n    print(x * 2)\nresult = compute(5)\n"
    assert len(_findings(src, "R-M5-02")) == 1


def test_rm5_03_flags_unreachable_statement():
    assert len(_findings("def f():\n    return 1\n    print('never')\n", "R-M5-03")) == 1


def test_rm5_03_does_not_flag_return_as_last_statement():
    assert len(_findings("def f():\n    x = 1\n    return x\n", "R-M5-03")) == 0


# ---- R-M6-01 -------------------------------------------------------------

def test_rm6_01_flags_module_level_read_of_function_local():
    assert len(_findings("def f():\n    secret = 42\nprint(secret)\n", "R-M6-01")) == 1


def test_rm6_01_does_not_flag_properly_returned_value():
    src = "def f():\n    secret = 42\n    return secret\nresult = f()\nprint(result)\n"
    assert len(_findings(src, "R-M6-01")) == 0


# ---- R-M6-02 -------------------------------------------------------------

def test_rm6_02_flags_read_before_local_assign_shadowing_global():
    src = (
        "total = 100\n"
        "def show():\n"
        "    print(total)\n"
        "    total = 5\n"
    )
    assert len(_findings(src, "R-M6-02")) == 1


def test_rm6_02_does_not_flag_with_global_declaration():
    src = (
        "total = 100\n"
        "def bump():\n"
        "    global total\n"
        "    print(total)\n"
        "    total = total + 1\n"
    )
    assert len(_findings(src, "R-M6-02")) == 0


def test_rm6_02_does_not_flag_when_no_read_before_assign():
    src = "total = 100\ndef reset():\n    total = 0\n    print(total)\n"
    assert len(_findings(src, "R-M6-02")) == 0


# ---- R-M6-03 -------------------------------------------------------------

def test_rm6_03_flags_unnecessary_reparameterisation():
    src = (
        "counter = 0\n"
        "def show(counter):\n"
        "    print(counter)\n"
        "show(counter)\n"
        "show(counter)\n"
    )
    assert len(_findings(src, "R-M6-03")) == 1


def test_rm6_03_does_not_flag_when_called_with_other_values():
    src = (
        "counter = 0\n"
        "def show(counter):\n"
        "    print(counter)\n"
        "show(5)\n"
    )
    assert len(_findings(src, "R-M6-03")) == 0


# ---- R-M7-01 -------------------------------------------------------------

def test_rm7_01_flags_missing_accumulator_init():
    src = "for n in [1, 2, 3]:\n    total += n\nprint(total)\n"
    assert len(_findings(src, "R-M7-01")) == 1


def test_rm7_01_does_not_flag_when_initialised():
    src = "total = 0\nfor n in [1, 2, 3]:\n    total += n\nprint(total)\n"
    assert len(_findings(src, "R-M7-01")) == 0


def test_rm7_01_does_not_flag_when_var_is_function_parameter():
    src = "def f(total):\n    for n in [1, 2, 3]:\n        total += n\n    return total\n"
    assert len(_findings(src, "R-M7-01")) == 0


# ---- R-M7-02 -------------------------------------------------------------

def test_rm7_02_flags_read_inside_loop_and_after():
    src = (
        "total = 0\n"
        "for n in [1, 2, 3]:\n"
        "    total += n\n"
        "    result = total\n"
        "print(total)\n"
    )
    assert len(_findings(src, "R-M7-02")) == 1


def test_rm7_02_does_not_flag_when_only_read_after_loop():
    src = "total = 0\nfor n in [1, 2, 3]:\n    total += n\nprint(total)\n"
    assert len(_findings(src, "R-M7-02")) == 0


def test_rm7_02_does_not_flag_debug_print_inside_loop():
    """
    Month 4 evaluation fix: the docstring always promised a lower
    confidence for a print()-fed read inside the loop, but the check
    never actually implemented it -- `total += n; print(total)` was
    flagged indistinguishably from a genuine premature-read mistake.
    Now suppressed outright, since printing a running value is a
    common, legitimate pattern and the frontend doesn't filter by
    confidence.
    """
    src = "total = 0\nfor n in [1, 2, 3]:\n    total += n\n    print(total)\nprint(total)\n"
    assert len(_findings(src, "R-M7-02")) == 0



def test_rm7_02_does_not_flag_running_total_in_fstring_print():
    src = (
        "total = 0\n"
        "for price in [4.99, 12.50]:\n"
        "    total += price\n"
        "    print(f'Running total so far: {total}')\n"
        "print(f'Final total: {total}')\n"
    )
    assert len(_findings(src, "R-M7-02")) == 0


# ---- R-M8-01 / R-M8-02 --------------------------------------------------

def test_rm8_01_flags_reassignment_of_sort_result():
    src = "my_list = [3, 1, 2]\nmy_list = my_list.sort()\n"
    findings = _findings(src, "R-M8-01")
    assert len(findings) == 1
    assert findings[0].confidence == "HIGH"


def test_rm8_01_does_not_flag_pop_reassignment():
    src = "my_list = [3, 1, 2]\nlast = my_list.pop()\n"
    assert len(_findings(src, "R-M8-01")) == 0


def test_rm8_02_flags_sort_call_as_print_argument():
    src = "my_list = [3, 1, 2]\nprint(my_list.sort())\n"
    assert len(_findings(src, "R-M8-02")) == 1


def test_rm8_02_does_not_flag_normal_statement_level_call():
    src = "my_list = [3, 1, 2]\nmy_list.sort()\nprint(my_list)\n"
    assert len(_findings(src, "R-M8-02")) == 0


def test_rm8_02_lowers_confidence_when_type_not_confirmed():
    """
    Month 4 evaluation fix: R-M8-02 previously always reported HIGH
    confidence regardless of type inference, unlike its sibling R-M8-01.
    A user-defined class with a same-named method (e.g. a fluent `.add()`
    returning `self`) is a real false-positive risk this brings back in
    line with R-M8-01's documented, already-accepted behavior.
    """
    src = (
        "class Cart:\n"
        "    def __init__(self):\n"
        "        self.items = []\n"
        "    def add(self, item):\n"
        "        self.items.append(item)\n"
        "        return self\n"
        "\n"
        "def describe(cart):\n"
        "    return str(cart.items)\n"
        "\n"
        "c = Cart()\n"
        "print(describe(c.add('apple')))\n"
    )
    findings = _findings(src, "R-M8-02")
    assert len(findings) == 1
    assert findings[0].confidence == "MEDIUM"


def test_rm8_02_keeps_high_confidence_when_type_confirmed():
    src = "items = []\ndef wrap(x):\n    return x\nprint(wrap(items.append(1)))\n"
    findings = _findings(src, "R-M8-02")
    assert len(findings) == 1
    assert findings[0].confidence == "HIGH"


# ---- R-M9-01 / R-M9-02 --------------------------------------------------

def test_rm9_01_flags_bare_attribute_statement():
    src = "my_list = [1, 2]\nmy_list.append\n"
    assert len(_findings(src, "R-M9-01")) == 1


def test_rm9_01_does_not_flag_actual_call():
    src = "my_list = [1, 2]\nmy_list.append(3)\n"
    assert len(_findings(src, "R-M9-01")) == 0


def test_rm9_02_flags_bare_function_name_statement():
    src = "def greet():\n    print('hi')\ngreet\n"
    assert len(_findings(src, "R-M9-02")) == 1


def test_rm9_02_does_not_flag_actual_call():
    src = "def greet():\n    print('hi')\ngreet()\n"
    assert len(_findings(src, "R-M9-02")) == 0


def test_rm9_02_does_not_flag_when_also_used_as_variable():
    src = "def greet():\n    pass\ngreet = 5\nprint(greet)\n"
    assert len(_findings(src, "R-M9-02")) == 0


# ---- R-M10-01 --------------------------------------------------------

def test_rm10_01_flags_unparenthesized_and_inside_or():
    src = "a = True\nb = False\nc = True\nif a and b or c:\n    pass\n"
    assert len(_findings(src, "R-M10-01")) == 1


def test_rm10_01_does_not_flag_when_parenthesized():
    src = "a = True\nb = False\nc = True\nif (a and b) or c:\n    pass\n"
    assert len(_findings(src, "R-M10-01")) == 0


def test_rm10_01_does_not_flag_plain_or():
    src = "a = True\nb = False\nif a or b:\n    pass\n"
    assert len(_findings(src, "R-M10-01")) == 0


# ---- R-M11-01 / R-M11-02 -----------------------------------------------

def test_rm11_01_flags_list_compared_to_none_for_emptiness():
    src = "my_list = []\nif my_list == None:\n    pass\n"
    assert len(_findings(src, "R-M11-01")) == 1


def test_rm11_01_does_not_flag_when_reassigned_to_none_first():
    src = "my_list = []\nmy_list = None\nif my_list == None:\n    pass\n"
    assert len(_findings(src, "R-M11-01")) == 0


def test_rm11_01_does_not_flag_non_container_variable():
    src = "x = 5\nif x == None:\n    pass\n"
    assert len(_findings(src, "R-M11-01")) == 0


def test_rm11_02_flags_bare_arithmetic_condition():
    assert len(_findings("x = 5\ny = 5\nif x - y:\n    pass\n", "R-M11-02")) == 1


def test_rm11_02_does_not_flag_modulo():
    assert len(_findings("x = 4\nif x % 2:\n    pass\n", "R-M11-02")) == 0


# ---- Registry-level sanity ---------------------------------------------

def test_all_22_rules_registered():
    assert len(ALL_RULES) == 22


def test_coverage_report_maps_every_rule_to_its_misconception():
    report = rule_coverage_report()
    assert report["R-M1-01"] == "M1"
    assert report["R-M10-01"] == "M10"
    assert len(report) == 22


def test_engine_never_crashes_on_a_realistic_mixed_snippet():
    src = (
        "def process(data):\n"
        "    results = []\n"
        "    for item in data:\n"
        "        results = item\n"
        "    return results\n"
        "\n"
        "x = [1, 2, 3]\n"
        "y = x\n"
        "y.append(4)\n"
        "print(x)\n"
    )
    findings = _findings(src)
    assert isinstance(findings, list)
    assert all(f.confidence != "ENGINE_ERROR" for f in findings)
