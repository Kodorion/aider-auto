"""
Unit tests for TCPEngine._get_symbols_with_frequencies.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aider.tcpe_engine import TCPEngine


@pytest.mark.unit
def test_get_symbols_empty_content(tcpe_engine: TCPEngine) -> None:
    """Scenario: _get_symbols_with_frequencies with empty content."""
    result = tcpe_engine._get_symbols_with_frequencies("", "test.py", "python", "")

    assert result == {}


@pytest.mark.unit
def test_get_symbols_parse_error(tcpe_engine: TCPEngine) -> None:
    """Scenario: _get_symbols_with_frequencies handles parse error."""
    with patch("aider.tcpe_engine.get_parser", side_effect=Exception("parse fail")):
        result = tcpe_engine._get_symbols_with_frequencies(
            "def foo():", "test.py", "python", ""
        )

    assert result == {}


@pytest.mark.unit
def test_get_symbols_python_code(tcpe_engine: TCPEngine) -> None:
    """Scenario: _get_symbols_with_frequencies with Python code."""
    content = "class MyClass:\n    def my_method(self):\n        pass\n"
    query_scm = "(function_definition name: (identifier) @name)"

    mock_parser = MagicMock()
    mock_tree = MagicMock()
    mock_root = MagicMock()
    mock_root.type = "module"
    mock_tree.root_node = mock_root
    mock_parser.parse.return_value = mock_tree

    mock_language = MagicMock()
    mock_query = MagicMock()

    mock_name_node = MagicMock()
    mock_name_node.text = b"my_method"
    mock_name_node.parent = MagicMock()
    mock_name_node.parent.parent = None
    mock_name_node.parent.child_by_field_name.return_value = MagicMock(text=b"MyClass")
    mock_name_node.parent.type = "class_definition"

    # QueryCursor.captures returns list of (node, tag_name) tuples
    mock_query.captures.return_value = [(mock_name_node, "name")]

    with (
        patch("aider.tcpe_engine.get_parser", return_value=mock_parser),
        patch("aider.tcpe_engine.get_language", return_value=mock_language),
        patch("aider.tcpe_engine.Query", return_value=mock_query),
    ):
        result = tcpe_engine._get_symbols_with_frequencies(content, "test.py", "python", query_scm)

    assert isinstance(result, dict)


@pytest.mark.unit
def test_get_symbols_cpp_overloads(tcpe_engine: TCPEngine) -> None:
    """Scenario: _get_symbols_with_frequencies with C++ function overloads."""
    content = "void func(int x) {}\nvoid func(string s) {}\n"
    query_scm = "(function_definition name: (identifier) @name parameters: (parameter_list) @params)"

    mock_parser = MagicMock()
    mock_tree = MagicMock()
    mock_root = MagicMock()
    mock_root.type = "translation_unit"
    mock_tree.root_node = mock_root
    mock_parser.parse.return_value = mock_tree

    mock_language = MagicMock()

    mock_name_node1 = MagicMock()
    mock_name_node1.text = b"func"
    mock_name_node1.parent = MagicMock()
    mock_name_node1.parent.id = 1
    mock_name_node1.parent.parent = None
    mock_params_node1 = MagicMock()
    mock_params_node1.text = b"(int x)"

    mock_name_node2 = MagicMock()
    mock_name_node2.text = b"func"
    mock_name_node2.parent = MagicMock()
    mock_name_node2.parent.id = 2
    mock_name_node2.parent.parent = None
    mock_params_node2 = MagicMock()
    mock_params_node2.text = b"(string s)"

    mock_query = MagicMock()
    # QueryCursor.captures returns flat list of (node, tag_name) tuples
    mock_query.captures.return_value = [
        (mock_name_node1, "name"),
        (mock_params_node1, "params"),
        (mock_name_node2, "name"),
        (mock_params_node2, "params"),
    ]

    with (
        patch("aider.tcpe_engine.get_parser", return_value=mock_parser),
        patch("aider.tcpe_engine.get_language", return_value=mock_language),
        patch("aider.tcpe_engine.Query", return_value=mock_query),
    ):
        result = tcpe_engine._get_symbols_with_frequencies(content, "test.cpp", "cpp", query_scm)

    assert isinstance(result, dict)
