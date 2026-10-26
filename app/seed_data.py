"""
Task bank: one small exercise per misconception (M1-M11).

target_misconceptions is design intent, not a detection filter -- every
submission is analyzed against all 22 rules regardless of task.

prompt vs. example: `prompt` is the instruction; `example` is a worked
example in full sentences, shown in its own box in the UI.

example_tests: shown to the student when a submission triggers zero
findings, so a clean scan comes with something concrete to check their
own work against instead of just a bare "looks fine" message. One test
case per line, plain text (not executed by the system).
"""

TASKS = [
    {
        "id": "T01",
        "title": "Repeated greeting",
        "prompt": (
            "Write a function greet_n_times(name, n) that returns a single "
            "string greeting 'name' n times, separated by commas."
        ),
        "example": (
            "Calling greet_n_times('Al', 3) should produce 'Hi Al, Hi Al, Hi Al' "
            "-- the greeting 'Hi Al' repeated three times, with a comma and a "
            "space between each repetition."
        ),
        "starter_code": "def greet_n_times(name, n):\n    # your code here\n    pass\n",
        "target_misconceptions": "M1",
        "example_tests": (
            "greet_n_times('Al', 3) -> 'Hi Al, Hi Al, Hi Al'\n"
            "greet_n_times('Sam', 1) -> 'Hi Sam'\n"
            "greet_n_times('Mo', 0) -> ''"
        ),
    },
    {
        "id": "T02",
        "title": "Swap two values",
        "prompt": (
            "Write a function swap(a, b) that returns a tuple with a and b "
            "swapped, using a temporary variable (no tuple unpacking)."
        ),
        "example": (
            "Calling swap(1, 2) should return (2, 1) -- the first value "
            "becomes the second, and the second becomes the first."
        ),
        "starter_code": "def swap(a, b):\n    # your code here\n    pass\n",
        "target_misconceptions": "M2",
        "example_tests": (
            "swap(1, 2) -> (2, 1)\n"
            "swap('x', 'y') -> ('y', 'x')"
        ),
    },
    {
        "id": "T03",
        "title": "Is it the same list?",
        "prompt": (
            "Write a function same_object(list_a, list_b) that returns True "
            "only if list_a and list_b are literally the same object in "
            "memory (not just equal in contents)."
        ),
        "example": (
            "If x = [1, 2] and you call same_object(x, x), it should return "
            "True, since both arguments refer to the exact same list. But "
            "same_object([1, 2], [1, 2]) should return False -- those are two "
            "separate lists that just happen to contain equal values."
        ),
        "starter_code": "def same_object(list_a, list_b):\n    # your code here\n    pass\n",
        "target_misconceptions": "M3",
        "example_tests": (
            "x = [1, 2]; same_object(x, x) -> True\n"
            "same_object([1, 2], [1, 2]) -> False  (equal contents, different objects)"
        ),
    },
    {
        "id": "T04",
        "title": "Count down",
        "prompt": (
            "Write a function countdown(n) that returns a list counting down "
            "from n to 1, inclusive."
        ),
        "example": (
            "Calling countdown(3) should return [3, 2, 1] -- starting at 3 and "
            "counting down one step at a time until reaching 1."
        ),
        "starter_code": "def countdown(n):\n    # your code here\n    pass\n",
        "target_misconceptions": "M4",
        "example_tests": (
            "countdown(3) -> [3, 2, 1]\n"
            "countdown(1) -> [1]\n"
            "countdown(0) -> []"
        ),
    },
    {
        "id": "T05",
        "title": "First even number",
        "prompt": (
            "Write a function first_even(numbers) that returns the first "
            "even number in the list. The caller uses the returned value, "
            "not any printed output."
        ),
        "example": (
            "Calling first_even([1, 3, 4, 6]) should return 4, since 4 is the "
            "first number in the list that is divisible by 2."
        ),
        "starter_code": "def first_even(numbers):\n    # your code here\n    pass\n",
        "target_misconceptions": "M5",
        "example_tests": (
            "first_even([1, 3, 4, 6]) -> 4\n"
            "first_even([2, 4]) -> 2\n"
            "first_even([1, 3]) -> None"
        ),
    },
    {
        "id": "T06",
        "title": "Track a high score",
        "prompt": (
            "Write update_high_score(current, new) that returns the higher "
            "of the two values, then write a small driver loop that reads "
            "several scores and keeps a running high score using this "
            "function inside a nested helper."
        ),
        "example": (
            "Calling update_high_score(10, 15) should return 15, since 15 is "
            "the larger of the two values."
        ),
        "starter_code": "def update_high_score(current, new):\n    # your code here\n    pass\n",
        "target_misconceptions": "M6",
        "example_tests": (
            "update_high_score(10, 15) -> 15\n"
            "update_high_score(20, 5) -> 20"
        ),
    },
    {
        "id": "T07",
        "title": "Total price",
        "prompt": (
            "Write a function total_price(prices) that returns the sum of "
            "all prices in the list, using an explicit loop (no sum())."
        ),
        "example": (
            "Calling total_price([1, 2, 3]) should return 6 -- the three "
            "prices added together, one at a time as the loop runs."
        ),
        "starter_code": "def total_price(prices):\n    # your code here\n    pass\n",
        "target_misconceptions": "M7",
        "example_tests": (
            "total_price([1, 2, 3]) -> 6\n"
            "total_price([]) -> 0\n"
            "total_price([5]) -> 5"
        ),
    },
    {
        "id": "T08",
        "title": "Sort a copy",
        "prompt": (
            "Write a function sorted_copy(items) that returns a NEW sorted "
            "list without modifying the original list passed in."
        ),
        "example": (
            "If x = [3, 1, 2] and you call sorted_copy(x), it should return "
            "[1, 2, 3]. Afterwards, x itself should still be [3, 1, 2] -- "
            "unchanged, because sorted_copy is not allowed to modify it."
        ),
        "starter_code": "def sorted_copy(items):\n    # your code here\n    pass\n",
        "target_misconceptions": "M8",
        "example_tests": (
            "x = [3, 1, 2]; sorted_copy(x) -> [1, 2, 3]\n"
            "after calling sorted_copy(x), x itself should STILL be [3, 1, 2]"
        ),
    },
    {
        "id": "T09",
        "title": "Shout it",
        "prompt": (
            "Write a function shout(sentence) that returns the sentence in "
            "uppercase, using the string's built-in method."
        ),
        "example": (
            "Calling shout('hello') should return 'HELLO' -- every letter "
            "converted to its uppercase form."
        ),
        "starter_code": "def shout(sentence):\n    # your code here\n    pass\n",
        "target_misconceptions": "M9",
        "example_tests": (
            "shout('hello') -> 'HELLO'\n"
            "shout('Already Loud') -> 'ALREADY LOUD'"
        ),
    },
    {
        "id": "T10",
        "title": "Average of three",
        "prompt": (
            "Write a function average(a, b, c) that returns the average of "
            "the three numbers, written as a single arithmetic expression."
        ),
        "example": (
            "Calling average(1, 2, 3) should return 2.0 -- the three numbers "
            "added together and divided by 3."
        ),
        "starter_code": "def average(a, b, c):\n    # your code here\n    pass\n",
        "target_misconceptions": "M10",
        "example_tests": (
            "average(1, 2, 3) -> 2.0\n"
            "average(0, 0, 9) -> 3.0"
        ),
    },
    {
        "id": "T11",
        "title": "Is the cart empty?",
        "prompt": (
            "Write a function is_cart_empty(cart) that returns True if the "
            "cart (a list of items) has zero items in it."
        ),
        "example": (
            "Calling is_cart_empty([]) should return True, since an empty "
            "list has no items. is_cart_empty(['apple']) should return False, "
            "since it has one item in it."
        ),
        "starter_code": "def is_cart_empty(cart):\n    # your code here\n    pass\n",
        "target_misconceptions": "M11",
        "example_tests": (
            "is_cart_empty([]) -> True\n"
            "is_cart_empty(['apple']) -> False"
        ),
    },
]

MISCONCEPTION_REFERENCE = {
    "M1": {"name": "Variable Persistence", "severity": 2},
    "M2": {"name": "Assignment Direction", "severity": 2},
    "M3": {"name": "Comparison-as-Assignment / Identity-vs-Equality", "severity": 2},
    "M4": {"name": "Loop Termination", "severity": 2},
    "M5": {"name": "Return Semantics", "severity": 3},
    "M6": {"name": "Scope", "severity": 3},
    "M7": {"name": "Accumulation Pattern", "severity": 1},
    "M8": {"name": "Mutation vs Return Value", "severity": 2},
    "M9": {"name": "Method Reference vs Method Call", "severity": 1},
    "M10": {"name": "Operator Precedence", "severity": 2},
    "M11": {"name": "Truthiness / Boolean-Numeric Conflation", "severity": 2},
}