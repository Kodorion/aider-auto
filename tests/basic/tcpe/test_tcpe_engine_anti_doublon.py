"""
Unit tests for TCPEngine.check_anti_doublon (AST Guardian).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aider.tcpe_engine import TCPEngine


@pytest.mark.unit
def test_anti_doublon_unknown_language(tcpe_engine: TCPEngine) -> None:
    """Scenario: check_anti_doublon handles unknown language."""
    with patch("aider.tcpe_engine.filename_to_lang", return_value=None):
        is_safe, error = tcpe_engine.check_anti_doublon("content", "file.unknown")

    assert is_safe is True
    assert error is None


@pytest.mark.unit
def test_anti_doublon_missing_query(tcpe_engine: TCPEngine) -> None:
    """Scenario: check_anti_doublon handles missing query."""
    with (
        patch("aider.tcpe_engine.filename_to_lang", return_value="python"),
        patch("aider.tcpe_engine.get_doublon_query", return_value=None),
    ):
        is_safe, error = tcpe_engine.check_anti_doublon("content", "file.py")

    assert is_safe is True
    assert error is None


@pytest.mark.unit
def test_anti_doublon_syntax_error(tcpe_engine: TCPEngine) -> None:
    """Scenario: check_anti_doublon handles syntax errors."""
    mock_parser = MagicMock()
    mock_tree = MagicMock()
    mock_tree.root_node.has_error = True
    mock_parser.parse.return_value = mock_tree

    with (
        patch("aider.tcpe_engine.filename_to_lang", return_value="python"),
        patch("aider.tcpe_engine.get_doublon_query", return_value="(identifier) @name"),
        patch("aider.tcpe_engine.get_parser", return_value=mock_parser),
    ):
        is_safe, error = tcpe_engine.check_anti_doublon("def broken(", "file.py")

    assert is_safe is False
    assert error is not None
    assert "Syntax error" in error


@pytest.mark.unit
def test_anti_doublon_allows_unique_symbols(tcpe_engine: TCPEngine) -> None:
    """Scenario: check_anti_doublon allows unique symbols."""
    mock_parser = MagicMock()
    mock_tree = MagicMock()
    mock_tree.root_node.has_error = False
    mock_parser.parse.return_value = mock_tree

    with (
        patch("aider.tcpe_engine.filename_to_lang", return_value="python"),
        patch("aider.tcpe_engine.get_doublon_query", return_value="(identifier) @name"),
        patch("aider.tcpe_engine.get_parser", return_value=mock_parser),
        patch.object(tcpe_engine, "_get_symbols_with_frequencies", return_value={"func1": 1}),
    ):
        is_safe, error = tcpe_engine.check_anti_doublon("def func1(): pass", "file.py", "")

    assert is_safe is True
    assert error is None


@pytest.mark.unit
def test_anti_doublon_blocks_duplicate_symbols(tcpe_engine: TCPEngine) -> None:
    """Scenario: check_anti_doublon blocks duplicate symbols."""
    with (
        patch("aider.tcpe_engine.filename_to_lang", return_value="python"),
        patch("aider.tcpe_engine.get_doublon_query", return_value="(identifier) @name"),
        patch("aider.tcpe_engine.get_parser", return_value=MagicMock()),
        patch.object(
            tcpe_engine,
            "_get_symbols_with_frequencies",
            side_effect=[{"func1": 1}, {"func1": 2}],
        ),
    ):
        is_safe, error = tcpe_engine.check_anti_doublon(
            "def func1(): pass\ndef func1(): pass", "file.py", "def func1(): pass"
        )

    assert is_safe is False
    assert error is not None
