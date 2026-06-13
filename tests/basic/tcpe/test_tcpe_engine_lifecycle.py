"""
Unit tests for TCPEngine lifecycle methods (track, timeout, resolve).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aider.tcpe_engine import TCPEngine


@pytest.mark.unit
def test_track_failed_block(tcpe_engine: TCPEngine) -> None:
    """Scenario: track_failed_block adds to failed_blocks."""
    tcpe_engine.track_failed_block("test.py", "new code")

    assert len(tcpe_engine.failed_blocks) == 1
    assert tcpe_engine.failed_blocks[0]["file"] == "test.py"
    assert tcpe_engine.failed_blocks[0]["replace"] == "new code"


@pytest.mark.unit
def test_increment_turn_and_timeout_increments(tcpe_engine: TCPEngine) -> None:
    """Scenario: increment_turn_and_timeout increments counter."""
    tcpe_engine.failed_blocks.append(
        {"file": "test.py", "replace": "code", "turns_unaddressed": 0}
    )
    coder_messages: list[dict] = []

    tcpe_engine.increment_turn_and_timeout(coder_messages)

    assert tcpe_engine.failed_blocks[0]["turns_unaddressed"] == 1
    assert len(tcpe_engine.failed_blocks) == 1


@pytest.mark.unit
def test_increment_turn_and_timeout_removes_abandoned(tcpe_engine: TCPEngine) -> None:
    """Scenario: increment_turn_and_timeout removes abandoned blocks."""
    tcpe_engine.failed_blocks.append(
        {"file": "test.py", "replace": "code", "turns_unaddressed": 2}
    )
    # coder_messages must be non-empty for timeout messages to be appended
    coder_messages: list[dict] = [{"role": "user", "content": "hello"}]

    tcpe_engine.increment_turn_and_timeout(coder_messages)

    assert len(tcpe_engine.failed_blocks) == 0
    assert len(coder_messages) == 2
    assert "abandoned" in coder_messages[1]["content"]


@pytest.mark.unit
def test_process_successful_edit_fuzzy_match(tcpe_engine: TCPEngine) -> None:
    """Scenario: process_successful_edit resolves fuzzy match."""
    tcpe_engine.failed_blocks.append(
        {"file": "test.py", "replace": "def foo(): pass", "turns_unaddressed": 0}
    )

    tcpe_engine.process_successful_edit("test.py", "def foo():  pass")

    assert len(tcpe_engine.failed_blocks) == 0


@pytest.mark.unit
def test_process_successful_edit_low_similarity(tcpe_engine: TCPEngine) -> None:
    """Scenario: process_successful_edit ignores low similarity."""
    tcpe_engine.failed_blocks.append(
        {"file": "test.py", "replace": "def foo(): pass", "turns_unaddressed": 0}
    )

    tcpe_engine.process_successful_edit("test.py", "def completely_different(): pass")

    assert len(tcpe_engine.failed_blocks) == 1
