"""
Unit tests for TCPEngine initialization and internal logging.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from aider.tcpe_engine import TCPEngine


@pytest.mark.unit
def test_tcpe_init_default_state(tcpe_engine: TCPEngine) -> None:
    """Scenario: Initialize TCPEngine with valid IO."""
    assert tcpe_engine.failed_blocks == []
    assert tcpe_engine.tcpe_log_path == ".tcpe_logs"


@pytest.mark.unit
def test_tcpe_log_creates_dir_and_writes_json(tcpe_engine: TCPEngine, tmp_path: Path) -> None:
    """Scenario: _log creates directory and writes JSON."""
    tcpe_engine.tcpe_log_path = str(tmp_path / "logs")
    event: str = "test_event"
    data: dict[str, str] = {"key": "value"}

    tcpe_engine._log(event, data)

    log_files = list(tmp_path.glob("**/tcpe_*.log"))
    assert len(log_files) == 1

    log_content = log_files[0].read_text()
    parsed: dict[str, Any] = json.loads(log_content.strip())
    assert parsed["event"] == event
    assert parsed["data"] == data


@pytest.mark.unit
def test_tcpe_log_handles_exception_silently(tcpe_engine: TCPEngine) -> None:
    """Scenario: _log handles exception silently."""
    with patch("os.path.exists", side_effect=PermissionError("no access")):
        tcpe_engine._log("test", {"key": "value"})

    # No exception should propagate


@pytest.mark.unit
def test_tcpe_init_sets_io_attribute(tcpe_engine: TCPEngine, mock_io: MagicMock) -> None:
    """Scenario: Initialize TCPEngine stores io reference."""
    assert tcpe_engine.io is mock_io
