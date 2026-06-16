"""Unit tests for the auto-prompt improvement feature in base_coder.Coder."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from aider.coders.base_coder import Coder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_io() -> MagicMock:
    """Provide a fresh mock InputOutput for each test."""
    io = MagicMock()
    io.confirm_ask.return_value = "y"
    io.tool_output = MagicMock()
    io.tool_warning = MagicMock()
    return io


@pytest.fixture
def mock_main_model() -> MagicMock:
    """Provide a fresh mock main_model for each test."""
    model = MagicMock()
    model.name = "gpt-4o"
    model.extra_params = None
    model.send_completion = MagicMock()
    return model


@pytest.fixture
def coder(
    mock_io: MagicMock,
    mock_main_model: MagicMock,
) -> Coder:
    """Build a minimal Coder instance with mocked dependencies.

    We patch heavy sub-systems (repo, linter, repo_map, summarizer) so that
    __init__ completes without side-effects.
    """
    with (
        patch.object(Coder, "__init__", lambda self, **kw: None),
    ):
        c: Any = object.__new__(Coder)
        c.auto_improve_prompt_enabled = True
        c.verbose = False
        c.io = mock_io
        c.main_model = mock_main_model
        c.commands = MagicMock()
        c.commands.is_command = MagicMock(return_value=False)
        c.tcpe = MagicMock()
        c.reflected_message = None
        c.num_reflections = 0
        c.max_reflections = 50
        c.cur_messages = []
        return c


# ---------------------------------------------------------------------------
# auto_improve_prompt() – early-exit paths
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_short_input_skipped(
    coder: Coder,
    mock_main_model: MagicMock,
) -> None:
    """Inputs shorter than 10 characters are returned unchanged."""
    result = coder.auto_improve_prompt("hello")
    assert result == "hello"
    mock_main_model.send_completion.assert_not_called()


@pytest.mark.unit
def test_command_input_skipped(
    coder: Coder,
    mock_main_model: MagicMock,
) -> None:
    """Inputs starting with '/' are returned unchanged."""
    result = coder.auto_improve_prompt("/status")
    assert result == "/status"
    mock_main_model.send_completion.assert_not_called()


@pytest.mark.unit
def test_disabled_flag_skips_improvement(
    coder: Coder,
    mock_main_model: MagicMock,
) -> None:
    """When auto_improve_prompt_enabled is False, skip improvement."""
    coder.auto_improve_prompt_enabled = False
    result = coder.auto_improve_prompt("this is a normal prompt that needs improvement")
    assert result == "this is a normal prompt that needs improvement"
    mock_main_model.send_completion.assert_not_called()


# ---------------------------------------------------------------------------
# auto_improve_prompt() – ###### block protection
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_only_blocks_no_other_text(
    coder: Coder,
    mock_main_model: MagicMock,
) -> None:
    """If input contains only ###### blocks, return original unchanged."""
    inp = "######\njust a block\n######"
    result = coder.auto_improve_prompt(inp)
    assert result == inp
    mock_main_model.send_completion.assert_not_called()


@pytest.mark.unit
def test_blocks_protected_and_appended(
    coder: Coder,
    mock_main_model: MagicMock,
) -> None:
    """###### blocks are extracted, remaining text improved, blocks appended."""
    inp = "fix this\n######\ncode block\n######"
    improved_text = "<task>Fix the issue</task>"
    completion = MagicMock()
    completion.choices[0].message.content = f"<improved_prompt>{improved_text}</improved_prompt>"

    with patch("aider.coders.base_coder.litellm.completion", return_value=completion) as mock_litellm:
        result = coder.auto_improve_prompt(inp)

        assert improved_text in result
        assert "######\ncode block\n######" in result
        assert "--- CONTEXT BLOCKS (original, unmodified) ---" in result
        mock_litellm.assert_called_once()


# ---------------------------------------------------------------------------
# auto_improve_prompt() – large input guard
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_large_input_confirmation_yes(
    coder: Coder,
    mock_io: MagicMock,
    mock_main_model: MagicMock,
) -> None:
    """Large input (>3000 chars) with user confirming 'y' proceeds."""
    long_input = "x" * 3001
    completion = MagicMock()
    completion.choices[0].message.content = "<improved_prompt><task>Improved long prompt</task></improved_prompt>"
    mock_io.confirm_ask.return_value = "y"

    with patch("aider.coders.base_coder.litellm.completion", return_value=completion) as mock_litellm:
        result = coder.auto_improve_prompt(long_input)

        assert result == "<task>Improved long prompt</task>"
        mock_io.confirm_ask.assert_called_once()
        mock_litellm.assert_called_once()


@pytest.mark.unit
def test_large_input_confirmation_no(
    coder: Coder,
    mock_io: MagicMock,
    mock_main_model: MagicMock,
) -> None:
    """Large input (>3000 chars) with user declining returns original."""
    long_input = "x" * 3001
    mock_io.confirm_ask.return_value = "n"

    result = coder.auto_improve_prompt(long_input)

    assert result == long_input
    mock_main_model.send_completion.assert_not_called()


# ---------------------------------------------------------------------------
# auto_improve_prompt() – LLM failure / fallback paths
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_llm_exception_fallback(
    coder: Coder,
    mock_io: MagicMock,
    mock_main_model: MagicMock,
) -> None:
    """If litellm.completion raises, return original and log warning."""
    original = "normal prompt text here"

    with patch("aider.coders.base_coder.litellm.completion", side_effect=Exception("API error")):
        result = coder.auto_improve_prompt(original)

        assert result == original
        mock_io.tool_warning.assert_called_once()
        warning_call = mock_io.tool_warning.call_args[0][0]
        assert "Prompt improvement failed" in warning_call
        assert "API error" in warning_call


@pytest.mark.unit
def test_llm_empty_response_fallback(
    coder: Coder,
    mock_main_model: MagicMock,
) -> None:
    """If LLM returns empty content, return original unchanged."""
    original = "normal prompt text here"
    completion = MagicMock()
    completion.choices[0].message.content = ""

    with patch("aider.coders.base_coder.litellm.completion", return_value=completion):
        result = coder.auto_improve_prompt(original)

        assert result == original


@pytest.mark.unit
def test_improved_too_short_fallback(
    coder: Coder,
    mock_io: MagicMock,
    mock_main_model: MagicMock,
) -> None:
    """If improved text has <10 non-whitespace chars, fall back."""
    original = "normal prompt text here"
    completion = MagicMock()
    completion.choices[0].message.content = "fix it"  # 6 non-ws chars

    with patch("aider.coders.base_coder.litellm.completion", return_value=completion):
        result = coder.auto_improve_prompt(original)

        assert result == original
        mock_io.tool_warning.assert_called_once()


@pytest.mark.unit
def test_improved_only_punctuation_fallback(
    coder: Coder,
    mock_io: MagicMock,
    mock_main_model: MagicMock,
) -> None:
    """If improved text is only punctuation, fall back."""
    original = "normal prompt text here"
    completion = MagicMock()
    completion.choices[0].message.content = "...!!?"

    with patch("aider.coders.base_coder.litellm.completion", return_value=completion):
        result = coder.auto_improve_prompt(original)

        assert result == original
        mock_io.tool_warning.assert_called_once()


# ---------------------------------------------------------------------------
# auto_improve_prompt() – success & verbose
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_normal_prompt_improved_success(
    coder: Coder,
    mock_main_model: MagicMock,
) -> None:
    """Normal prompt returns improved text from LLM."""
    original = "fix the bug in my code"
    improved = "<task>Fix the bug in the code</task>"
    completion = MagicMock()
    completion.choices[0].message.content = f"<improved_prompt>{improved}</improved_prompt>"

    with patch("aider.coders.base_coder.litellm.completion", return_value=completion) as mock_litellm:
        result = coder.auto_improve_prompt(original)

        assert result == improved
        mock_litellm.assert_called_once()


@pytest.mark.unit
def test_verbose_logs_improved_prompt(
    coder: Coder,
    mock_io: MagicMock,
    mock_main_model: MagicMock,
) -> None:
    """Verbose mode logs the improved prompt."""
    coder.verbose = True
    original = "normal prompt text here"
    improved = "<task>Improved</task>"
    completion = MagicMock()
    completion.choices[0].message.content = f"<improved_prompt>{improved}</improved_prompt>"

    with patch("aider.coders.base_coder.litellm.completion", return_value=completion):
        coder.auto_improve_prompt(original)

        mock_io.tool_output.assert_called()
        calls_str = " ".join(str(c) for c in mock_io.tool_output.call_args_list)
        assert "Improved prompt:" in calls_str


# ---------------------------------------------------------------------------
# preproc_user_input() – /noimprove bypass & integration
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_preproc_noimprove_bypass(
    coder: Coder,
) -> None:
    """/noimprove strips prefix and skips auto_improve_prompt."""
    with patch.object(coder, "auto_improve_prompt") as mock_improve:
        with patch.object(coder, "check_for_file_mentions") as mock_mentions:
            with patch.object(coder, "check_for_urls", return_value="fix the bug") as mock_urls:
                result = coder.preproc_user_input("/noimprove fix the bug")

                mock_improve.assert_not_called()
                mock_mentions.assert_called_once()
                assert result == "fix the bug"


@pytest.mark.unit
def test_preproc_normal_flow_calls_improve(
    coder: Coder,
) -> None:
    """Normal input flows through auto_improve_prompt."""
    original = "fix the bug"
    improved = "<task>Fix the bug</task>"

    with patch.object(coder, "auto_improve_prompt", return_value=improved) as mock_improve:
        with patch.object(coder, "check_for_file_mentions"):
            with patch.object(coder, "check_for_urls", return_value=improved):
                result = coder.preproc_user_input(original)

                mock_improve.assert_called_once_with(original)
                assert result == improved


# ---------------------------------------------------------------------------
# Integration test – full pipeline
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_full_pipeline_improved_prompt_sent_to_main_llm(
    coder: Coder,
    mock_main_model: MagicMock,
) -> None:
    """Integration: Verify improved prompt flows through to send_message."""
    original = "fix the bug"
    improved = "<task>Fix the bug in the code</task>"
    completion = MagicMock()
    completion.choices[0].message.content = f"<improved_prompt>{improved}</improved_prompt>"

    # Mock the downstream methods
    with patch("aider.coders.base_coder.litellm.completion", return_value=completion) as mock_litellm:
        with patch.object(coder, "check_for_file_mentions", return_value=None):
            with patch.object(coder, "check_for_urls", return_value=improved):
                result = coder.preproc_user_input(original)

                # Verify auto_improve_prompt was called and returned improved text
                assert result == improved
                mock_litellm.assert_called_once()

                # Verify the improved prompt (not original) was used
                call_args = mock_litellm.call_args
                messages = call_args[1]["messages"]
                user_msg = messages[1]["content"]
                assert user_msg == original  # The sanitized text sent to improve LLM


@pytest.mark.unit
def test_run_one_uses_improved_prompt(
    coder: Coder,
    mock_main_model: MagicMock,
) -> None:
    """Integration: run_one should use the improved prompt from preproc."""
    original = "fix the bug"
    improved = "<task>Fix the bug in the code</task>"
    completion = MagicMock()
    completion.choices[0].message.content = f"<improved_prompt>{improved}</improved_prompt>"
    mock_main_model.send_completion.return_value = ("hash", completion)

    with patch.object(coder, "check_for_file_mentions", return_value=None):
        with patch.object(coder, "check_for_urls", return_value=improved):
            with patch.object(coder, "send_message") as mock_send:
                mock_send.return_value = iter([])
                with patch.object(coder, "init_before_message"):
                    coder.run_one(original, preproc=True)

                    # Verify send_message was called with the improved prompt
                    mock_send.assert_called_once()
                    call_arg = mock_send.call_args[0][0]
                    assert call_arg == improved


# ---------------------------------------------------------------------------
# auto_improve_prompt() – XML Stripping Edge Cases
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_strips_markdown_wrapped_xml(
    coder: Coder,
    mock_main_model: MagicMock,
) -> None:
    """If the LLM wraps the XML in markdown code blocks, strip them safely."""
    original = "fix the bug"
    # LLM returns markdown wrapped XML
    mock_response = "```xml\n<improved_prompt><task>Fix the bug</task></improved_prompt>\n```"
    completion = MagicMock()
    completion.choices[0].message.content = mock_response

    with patch("aider.coders.base_coder.litellm.completion", return_value=completion):
        result = coder.auto_improve_prompt(original)

        assert result == "<task>Fix the bug</task>"


@pytest.mark.unit
def test_handles_empty_xml_wrapper_fallback(
    coder: Coder,
    mock_io: MagicMock,
    mock_main_model: MagicMock,
) -> None:
    """If the LLM returns an empty XML wrapper, fallback to the original prompt."""
    original = "normal prompt text here"
    completion = MagicMock()
    completion.choices[0].message.content = "<improved_prompt></improved_prompt>"

    with patch("aider.coders.base_coder.litellm.completion", return_value=completion):
        result = coder.auto_improve_prompt(original)

        # Because the stripped result is empty, it should trigger the `if not improved:` fallback
        assert result == original
