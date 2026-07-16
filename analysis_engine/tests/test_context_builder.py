import ast

from analysis_engine.context_builder import build_context


def _ctx(source: str):
    return build_context(ast.parse(source), source=source)


def test_module_scope_tracks_assignments():
    ctx = _ctx("x = 1\ny = 2\n")
    assert "x" in ctx.module_scope.assigned_names
    assert "y" in ctx.module_scope.assigned_names


def test_function_gets_its_own_scope():
    ctx = _ctx("def f(a, b):\n    c = a + b\n    return c\n")
    assert "f" in ctx.functions
    finfo = ctx.functions["f"]
    assert finfo.params == ["a", "b"]
    assert "c" in finfo.scope.assigned_names
    assert len(finfo.returns) == 1


def test_nested_function_does_not_leak_into_loop_body_names():
    src = (
        "for i in range(3):\n"
        "    def helper():\n"
        "        z = 1\n"
        "    total = i\n"
    )
    ctx = _ctx(src)
    assert len(ctx.loops) == 1
    loop = ctx.loops[0]
    assert "total" in loop.body_assigned_names
    assert "z" not in loop.body_assigned_names  # z belongs to helper's scope


def test_while_loop_test_names_collected():
    ctx = _ctx("i = 0\nwhile i < 5:\n    print(i)\n")
    assert len(ctx.loops) == 1
    assert ctx.loops[0].test_names == {"i"}


def test_for_loop_test_names_empty():
    ctx = _ctx("for i in range(5):\n    print(i)\n")
    assert ctx.loops[0].test_names == set()


def test_inferred_type_list():
    ctx = _ctx("results = []\n")
    key = (id(ctx.module_scope), "results")
    assert ctx.inferred_types[key] == "list"


def test_inferred_type_str_int():
    ctx = _ctx("name = 'hi'\ncount = 3\n")
    assert ctx.inferred_types[(id(ctx.module_scope), "name")] == "str"
    assert ctx.inferred_types[(id(ctx.module_scope), "count")] == "int"


def test_global_declaration_tracked():
    src = "counter = 0\ndef bump():\n    global counter\n    counter += 1\n"
    ctx = _ctx(src)
    assert "counter" in ctx.functions["bump"].scope.global_declarations


def test_calls_by_name_collected():
    ctx = _ctx("print('a')\nprint('b')\nlen([1, 2])\n")
    assert len(ctx.calls_by_name["print"]) == 2
    assert len(ctx.calls_by_name["len"]) == 1


def test_loop_tracks_aug_assign_separately_from_assign():
    ctx = _ctx("total = 0\nfor n in [1, 2]:\n    total += n\n")
    loop = ctx.loops[0]
    assert "total" in loop.body_aug_assigned_names
    assert "total" not in loop.body_assigned_names


def test_source_is_stored_on_context():
    src = "x = 1\n"
    ctx = _ctx(src)
    assert ctx.source == src
