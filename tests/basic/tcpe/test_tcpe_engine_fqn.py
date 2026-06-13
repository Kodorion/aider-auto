"""
Unit tests for TCPEngine._get_node_fqn (Fully Qualified Name extraction).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aider.tcpe_engine import TCPEngine


@pytest.mark.unit
def test_get_node_fqn_simple_identifier(tcpe_engine: TCPEngine) -> None:
    """Scenario: _get_node_fqn with simple identifier (no parent)."""
    node = MagicMock()
    node.parent = None
    node.text = b"simple_name"

    result = tcpe_engine._get_node_fqn(node)

    assert result == "simple_name"


@pytest.mark.unit
def test_get_node_fqn_class_method(tcpe_engine: TCPEngine) -> None:
    """Scenario: _get_node_fqn with class method."""
    method_node = MagicMock()
    method_node.text = b"method_name"

    class_node = MagicMock()
    class_node.parent = None
    class_node.child_by_field_name.return_value = MagicMock(text=b"ClassName")
    class_node.type = "class_definition"

    method_node.parent = class_node

    result = tcpe_engine._get_node_fqn(method_node)

    assert "ClassName" in result
    assert "method_name" in result


@pytest.mark.unit
def test_get_node_fqn_nested_scopes(tcpe_engine: TCPEngine) -> None:
    """Scenario: _get_node_fqn with nested scopes."""
    inner_node = MagicMock()
    inner_node.text = b"inner_method"

    inner_class = MagicMock()
    inner_class.child_by_field_name.return_value = MagicMock(text=b"InnerClass")
    inner_class.type = "class_definition"

    outer_class = MagicMock()
    outer_class.parent = None
    outer_class.child_by_field_name.return_value = MagicMock(text=b"OuterClass")
    outer_class.type = "class_definition"

    inner_class.parent = outer_class
    inner_node.parent = inner_class

    result = tcpe_engine._get_node_fqn(inner_node)

    assert "OuterClass" in result
    assert "InnerClass" in result
    assert "inner_method" in result
