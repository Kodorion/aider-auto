"""
Integration tests for TCPEngine hooks wired into the Coder edit lifecycle.

These tests verify that TCPEngine methods (track_failed_block, check_anti_doublon,
process_successful_edit, scrub_message, extract_modified_symbols) are invoked
at the correct points during the edit flow, WITHOUT modifying the core implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from aider.coders.base_coder import Coder
from aider.coders.editblock_coder import EditBlockCoder
from aider.tcpe_engine import TCPEngine


# ---------------------------------------------------------------------------
# Helper: build a minimal EditBlockCoder with all external deps mocked
# ---------------------------------------------------------------------------


def _make_coder() -> tuple[EditBlockCoder, MagicMock, MagicMock]:
    """Return (coder, mock_io, mock_main_model) ready for integration tests."""
    mock_io = MagicMock()
    mock_io.pretty = False
    mock_io.encoding = "utf-8"
    mock_io.multiline_mode = False
    mock_io.chat_history_file = str(Path(".aider.chat.history.md"))

    mock_main_model = MagicMock()
    mock_main_model.name = "gpt-4-test"
    mock_main_model.edit_format = "diff"
    mock_main_model.streaming = False
    mock_main_model.use_repo_map = False
    mock_main_model.system_prompt_prefix = None
    mock_main_model.examples_as_sys_msg = False
    mock_main_model.use_system_prompt = True
    mock_main_model.reminder = "sys"
    mock_main_model.lazy = False
    mock_main_model.overeager = False
    mock_main_model.reasoning_tag = None
    mock_main_model.caches_by_default = False
    mock_main_model.info = {
        "max_input_tokens": 128_000,
        "max_output_tokens": 8_192,
        "input_cost_per_token": 0.0,
        "output_cost_per_token": 0.0,
    }
    mock_main_model.weak_model = mock_main_model
    mock_main_model.max_chat_history_tokens = 16_000
    mock_main_model.commit_message_models.return_value = [mock_main_model]
    mock_main_model.token_count.return_value = 100
    mock_main_model.get_thinking_tokens.return_value = None
    mock_main_model.get_reasoning_effort.return_value = None
    mock_main_model.get_repo_map_tokens.return_value = 1024

    with (
        patch("aider.coders.base_coder.GitRepo"),
        patch("aider.coders.base_coder.RepoMap"),
        patch("aider.coders.base_coder.ChatSummary"),
        patch("aider.coders.base_coder.Linter"),
        patch("aider.coders.base_coder.Analytics"),
    ):
        coder = EditBlockCoder(
            main_model=mock_main_model,
            io=mock_io,
            use_git=False,
            map_tokens=0,
        )

    # Enable TCPEngine feature gate
    coder.tcpe_enabled = True

    # Ensure gpt_prompts exists (EditBlockCoder sets it via class attr)
    if not hasattr(coder, "gpt_prompts"):
        coder.gpt_prompts = MagicMock()
        coder.gpt_prompts.main_system = "Test system prompt"
        coder.gpt_prompts.system_reminder = None
        coder.gpt_prompts.example_messages = []
        coder.gpt_prompts.files_content_prefix = ""
        coder.gpt_prompts.files_content_assistant_reply = "Ok."
        coder.gpt_prompts.files_no_full_files = "No files."
        coder.gpt_prompts.files_no_full_files_with_repo_map = None
        coder.gpt_prompts.files_no_full_files_with_repo_map_reply = None
        coder.gpt_prompts.read_only_files_prefix = ""
        coder.gpt_prompts.repo_content_prefix = None
        coder.gpt_prompts.lazy_prompt = None
        coder.gpt_prompts.overeager_prompt = None
        coder.gpt_prompts.shell_cmd_prompt = ""
        coder.gpt_prompts.shell_cmd_reminder = ""
        coder.gpt_prompts.no_shell_cmd_prompt = ""
        coder.gpt_prompts.no_shell_cmd_reminder = ""
        coder.gpt_prompts.rename_with_shell = ""
        coder.gpt_prompts.go_ahead_tip = ""
        coder.gpt_prompts.files_content_gpt_edits = "Edits applied."
        coder.gpt_prompts.files_content_gpt_edits_no_repo = None
        coder.gpt_prompts.files_content_gpt_no_edits = "No edits."

    return coder, mock_io, mock_main_model


# ---------------------------------------------------------------------------
# Test 1: Hooks fire on failed edit
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_hooks_fire_on_failed_edit() -> None:
    """
    Scenario: When apply_edits encounters a failed SEARCH/REPLACE block,
    track_failed_block should be invoked before ValueError is raised.
    """
    coder, mock_io, _ = _make_coder()

    # Spy on the TCPEngine method
    with patch.object(coder.tcpe, "track_failed_block") as mock_track:
        # Prepare a fake edit that will fail (file does not exist, original non-empty)
        fake_edit = ("nonexistent_file.py", "def foo():\n    pass\n", "def bar():\n    pass\n")

        # Mock io.read_text to return content that won't match the SEARCH block
        mock_io.read_text.return_value = "def something_else():\n    return 42\n"

        # apply_edits raises ValueError when all edits fail — expect it
        with pytest.raises(ValueError):
            coder.apply_edits([fake_edit])

    # Verify track_failed_block was called for the failed edit
    mock_track.assert_called()
    call_args = mock_track.call_args
    assert call_args[0][0] == "nonexistent_file.py"


# ---------------------------------------------------------------------------
# Test 2: Hooks fire on successful edit
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_hooks_fire_on_successful_edit() -> None:
    """
    Scenario: When apply_edits successfully applies a SEARCH/REPLACE block,
    check_anti_doublon and process_successful_edit should be invoked.
    """
    coder, mock_io, _ = _make_coder()

    original_content = "def foo():\n    pass\n"
    updated_content = "def foo():\n    return 42\n"
    fake_edit = ("test_file.py", original_content, updated_content)

    # Mock file existence and content
    mock_io.read_text.return_value = original_content

    # Spy on TCPEngine methods
    with (
        patch.object(coder.tcpe, "check_anti_doublon", return_value=(True, None)) as mock_check,
        patch.object(coder.tcpe, "process_successful_edit") as mock_process,
        patch.object(coder.tcpe, "extract_modified_symbols", return_value=[]) as mock_extract,
        patch.object(coder.tcpe, "scrub_message", side_effect=lambda m, *a: m) as mock_scrub,
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.touch"),
    ):
        coder.apply_edits([fake_edit])

    # Verify anti-doublon check was called
    mock_check.assert_called()

    # Verify success resolver was called
    mock_process.assert_called()
    call_args = mock_process.call_args
    assert call_args[0][0] == "test_file.py"


# ---------------------------------------------------------------------------
# Test 3: Scrub message in history
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_scrub_message_in_history() -> None:
    """
    Scenario: When a successful edit is applied, extract_modified_symbols and
    scrub_message should be invoked to compress the assistant's chat history.
    """
    coder, mock_io, _ = _make_coder()

    original_content = "def foo():\n    pass\n"
    updated_content = "def foo():\n    return 42\n"
    fake_edit = ("test_file.py", original_content, updated_content)

    # Populate cur_messages with an assistant message containing a SEARCH/REPLACE block
    search_replace_block = (
        f"<<<<<<< SEARCH\n{original_content}"
        f"=======\n{updated_content}"
        f">>>>>>> REPLACE"
    )
    coder.cur_messages = [
        {"role": "assistant", "content": search_replace_block},
    ]

    # Mock file existence and content
    mock_io.read_text.return_value = original_content

    # Spy on TCPEngine methods
    with (
        patch.object(coder.tcpe, "check_anti_doublon", return_value=(True, None)),
        patch.object(coder.tcpe, "extract_modified_symbols", return_value=["foo"]) as mock_extract,
        patch.object(coder.tcpe, "scrub_message", side_effect=lambda m, *a: m) as mock_scrub,
        patch.object(coder.tcpe, "process_successful_edit"),
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.touch"),
    ):
        coder.apply_edits([fake_edit])

    # Verify extract_modified_symbols was called
    mock_extract.assert_called()
    extract_call = mock_extract.call_args
    assert extract_call[0][0] == "test_file.py"

    # Verify scrub_message was called
    mock_scrub.assert_called()
    scrub_call = mock_scrub.call_args
    assert scrub_call[0][1] == "test_file.py"
