from analysis_engine.parser import parse_source, dump_tree


def test_valid_code():
    result = parse_source("x = 1 + 2\n")
    assert result.success is True
    assert result.tree is not None
    assert result.error is None


def test_broken_code():
    result = parse_source("if x == 1\n    print('hi')\n")
    assert result.success is False
    assert result.tree is None
    assert result.error is not None
    assert result.error.line == 1


def test_empty_code():
    result = parse_source("")
    assert result.success is True
    assert result.tree.body == []


def test_dump_tree_matches_manual_ast_dump():
    import ast
    result = parse_source("x = 1\n")
    assert dump_tree(result.tree) == ast.dump(ast.parse("x = 1\n"), indent=2)
