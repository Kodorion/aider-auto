Aider Fork: Autonomous Coding with Safety & Efficiency

This fork transforms Aider into an hours‑long autonomous agent with command whitelisting (no --yes), aggressive log compression, XML prompts, and auto-testing.

Short version: This fork aims to turn Aider into an hours‑long autonomous agent that writes, tests, and fixes code without human intervention, only supervision. It adds a command whitelist (no --yes dangers), aggressive log compression, especially on successful command output, XML prompt structuring, and an auto‑test system. Perfect for running overnight refactoring or implementing a detailed plan. Works well with a todo.md. For the full list of changes, scroll down.

Table of Contents

🌟 What's different from standard Aider?

🚀 Quick Start & Setup

⚙️ Core Configuration & Whitelists

🗜️ Smart Log Compression Engine

🧠 XML Prompts & Core Logic Changes

⚠️ Known Issues & Caveats

🌟 What's different from standard Aider?

No --yes – uses a whitelist of safe commands (pytest, git status, cargo check, etc.) to prevent destructive actions.

Auto-testing – runs mirror unit tests after every change, with token-efficient output.

Auto-prompt improvement – automatically reformulates user prompts to be clearer, more precise, and more effective before sending to the main LLM. Displays the improved prompt in the UI for transparency. Disable with `--no-auto-improve` or bypass per-message with `/noimprove`.

XML prompts – enforces plan-first logic to cleanly separate reasoning from code blocks, reducing malformed edits.

Log compression – cuts massive error logs from thousands of tokens down to a few critical lines.

Anti-duplicate system – prevents the LLM from appending duplicate code blocks in Python and Rust using structural check comparisons.

Context management – the agent can autonomously request to add or drop files from its context window.

🚀 Quick Start & Setup

To fully utilize the autonomous testing loops and specific LLM behaviors introduced in this fork, you should set up your configuration, test script, and launch parameters.

Note: Both smart_test.py and the aider.bat example can be found in the root directory of this Aider fork for easy retrieval. These are example files. Copy them to your project as needed.

1. Configuration (.aider.conf.yml)

Create a .aider.conf.yml in the root of your project repository (where you run Aider) and add:

test-cmd: python smart_test.py


2. Ignore Files (.gitignore)

To ensure Aider's logs and history files don't clutter your git commits, add the following to the .gitignore in your project's root:

__pycache__/
*.pyc
.pytest_cache/
.aider.run.last.log
.aider.llm.history


3. Test Wrapper (smart_test.py)

Copy the smart_test.py script from the Aider fork root and place it directly in your project root.

Note: For Python, this script relies on a mirrored test architecture (e.g., src/module.py matching tests/unit/module.py or tests/test_module.py) to smartly target tests based on git status.

4. Recommended Launch Script (aider.bat / .sh)

Because we use virtual environments and require specific Python versions, we highly recommend launching Aider via a shell script or alias.

For Windows Users: Copy the included aider.bat and place it in your local user binaries directory (e.g., C:\Users\[PC-NAME]\.local\bin\aider.bat).

@echo off

:: 1. CACHE PROTECTION
set AIDER_DIVERSIFY_PROMPTS=false

:: 2. LAUNCH WITH EXPLICIT FLAGS
python -m aider --llm-history-file .aider.llm.history --edit-format diff --chat-language English --commit-language English --no-auto-commits --cache-prompts --auto-test --dark-mode --no-show-model-warnings %*


For Linux/macOS Users: Create an equivalent bash alias or .sh script using the same flags from step 2 above.

⚙️ Core Configuration & Whitelists

To prevent the agent from getting stuck on Y/n (yes/no) prompts during autonomous loops, you can configure command bypasses.

1. Command Whitelists (YOLO Mode)

If you need to add or remove commands that the agent is allowed to run without human confirmation, you must explicitly edit these two files in the Aider source:

aider/io.py: Search for the confirm_ask method. Inside this method, add or remove commands in the safe_prefixes list (e.g., "pytest", "cargo test", "python", "black").

aider/coders/base_coder.py: Search for the handle_shell_commands function. There is an additional safe_prefixes tuple here that auto-approves diagnostic commands.

2. Bypassing Log Compression (OUTPUT_EXCEPTIONS)

Sometimes you want the LLM to read a massive log without compressing it.

Where to edit: Open aider/coders/base_coder.py and search for the OUTPUT_EXCEPTIONS dictionary near the top of the Coder class definition.

How it works: Add specific substrings that, if found in the command or the output, will completely bypass the log compression engine. Current defaults include "ENERGY BALANCE SHEET", "mut_run.py", and "### High-Density Metrics".

🗜️ Smart Log Compression Engine

The system uses precise extraction math to prevent terminal output from overflowing the LLM context window:

Trigger Thresholds: Any output exceeding 1000 tokens is flagged for compression.

Hard Truncation (OOM Safety): If an output exceeds 1MB (1,048,576 bytes), it is hard-truncated to 512KB at the start and 512KB at the end to prevent memory crashes.

Error Extraction Math:

Searches the output for Error, Traceback, Panic, Exception, etc.

Captures 3 lines before and 15 lines after each matched error zone.

Preserves the top 10 lines (Head) and bottom 15 lines (Tail) of the log.

Caps the extracted "middle" block to a maximum budget of 15,000 characters.

Unabridged Backup: No matter how heavily compressed the sent message is, the full raw log is always written to .aider.run.last.log in your repository root.

🧠 XML Prompts & Core Logic Changes

To improve LLM adherence, standard markdown prompts were replaced with strict XML system boundaries (<role>, <execution_protocol>, etc.).

The <action_plan> Anchor: In the EditBlock prompt (which produces DIFFs), the agent is now strictly required to write an <action_plan> block before outputting any SEARCH/REPLACE blocks. This forces the LLM to separate its "reasoning phase" from its "code generation phase", drastically reducing malformed edits.

Autonomous File Context: The agent can manage its own context window dynamically.

Outputting <file_request>path/to/file</file_request> will auto-add a file.

Outputting <file_drop>path/to/file</file_drop> will auto-remove a file to free up tokens.

⚠️ Known Issues & Caveats

Because this logic was AI-generated, there are a few unresolved edge cases currently under investigation:

Windows bash Reliance: The agent is instructed to output commands inside ```bash code blocks. However, the execution environment expects this to function correctly natively. This was developed and tested on a Windows environment, so executing shell commands heavily relies on how Windows interprets the bash commands (or falls back appropriately).

Single-Word Replies: We don’t know if it’s caused by the use of local quantized LLMs or from our changes, but sometimes the agent replies with a single word and needs manual input to restart the loop.
