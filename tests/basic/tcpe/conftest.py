"""
Shared fixtures for TCPEngine unit tests.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from aider.tcpe_engine import TCPEngine


@pytest.fixture
def mock_io() -> MagicMock:
    """Provide a mocked InputOutput instance for TCPEngine tests."""
    io = MagicMock()
    io.tool_warning = MagicMock()
    return io


@pytest.fixture
def tcpe_engine(mock_io: MagicMock) -> TCPEngine:
    """Provide a fresh TCPEngine instance backed by mock_io."""
    return TCPEngine(mock_io)
