"""
Unit tests for TCPEngine.scrub_message (Semantic Summarization).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aider.tcpe_engine import TCPEngine


@pytest.mark.unit
def test_scrub_message_exact_block_match(tcpe_engine: TCPEngine) -> None:
    """Scenario: scrub_message with exact block match."""
    original = "old code"
    updated = "new code"
    message = f"Hello\n<<<<<<< SEARCH\n{original}=======\n{updated}>>>>>>> REPLACE\nDone"

    result = tcpe_engine.scrub_message(message, "test.py", [], original, updated)

    assert "<<<<<<< SEARCH" not in result
    assert "[SYSTEM LOG:" in result


@pytest.mark.unit
def test_scrub_message_no_blocks(tcpe_engine: TCPEngine) -> None:
    """Scenario: scrub_message with no blocks."""
    message = "Just a plain message without any blocks."

    result = tcpe_engine.scrub_message(message, "test.py", [], "original", "updated")

    assert result == message


@pytest.mark.unit
def test_scrub_message_with_modified_symbols(tcpe_engine: TCPEngine) -> None:
    """Scenario: scrub_message with modified symbols."""
    original = "old code"
    updated = "new code"
    message = f"Hello\n<<<<<<< SEARCH\n{original}=======\n{updated}>>>>>>> REPLACE\nDone"
    modified_symbols = ["func1", "func2", "func3", "func4"]

    result = tcpe_engine.scrub_message(message, "test.py", modified_symbols, original, updated)

    assert "func1" in result
    assert "func2" in result
    assert "func3" in result
    assert "and 1 sub-elements" in result


@pytest.mark.unit
def test_scrub_message_empty_content(tcpe_engine: TCPEngine) -> None:
    """Scenario: scrub_message with empty content."""
    result = tcpe_engine.scrub_message("", "test.py", [], "original", "updated")

    assert result == ""


@pytest.mark.unit
def test_scrub_message_fuzzy_block_match(tcpe_engine: TCPEngine) -> None:
    """Scenario: scrub_message with fuzzy block match (modified block content)."""
    original = "old code"
    updated = "new code"
    message = f"Hello\n<<<<<<< SEARCH\n{original} extra stuff =======\n{updated}>>>>>>> REPLACE\nDone"

    result = tcpe_engine.scrub_message(message, "test.py", [], original, updated)

    assert "[SYSTEM LOG:" in result
