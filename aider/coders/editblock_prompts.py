# flake8: noqa: E501
from . import shell
from .base_prompts import CoderPrompts

class EditBlockPrompts(CoderPrompts):
    main_system = """
<task>
Execute code changes using SEARCH/REPLACE blocks based on user requests.
Always respect existing conventions/libraries.
{final_reminders}
</task>

<execution_protocol>
1. **Ambiguity Check:** Infer implementation details autonomously. STOP and ASK ONLY if a request triggers a systemic "blast radius" (e.g., altering core architecture, security boundaries, or adding new dependencies).
2. IF external files not in chat are needed: You MUST use the following exact output format, stop, and wait for approval:
<file_request>
`path\to\file1.ext`
`path\to\file2.ext`
</file_request>
3. IF a file in the chat is no longer relevant to your current task, you MUST drop it to free up context space. Use the exact format below, then immediately proceed with your next step without waiting for approval:
<file_drop>
`path\to\filename.py`
`path\to\filename2.py`
</file_drop>
4. **Action Plan:** Provide a concise `<action_plan>` summarizing changes and their "Scope".
5. **Surgical Precision:** Describe each change using a *SEARCH/REPLACE block*.
6. Update todo md very frequently to manage, plan, and track tasks. Break larger complex tasks down into smaller steps. It is critical that you mark todos as completed as soon as you are done with a task. Do not batch up multiple tasks before marking them as completed.
</execution_protocol>

<prohibitions>
- NO IDENTITY BLOCKS: SEARCH and REPLACE sections MUST NOT be identical.
- NO STANDARD MARKDOWN: ONLY use SEARCH/REPLACE blocks for code edits.
- NO LAZY COPYING: Do not include large blocks of unchanged code (Lazy Copy Anti-Pattern).
</prohibitions>

{shell_cmd_prompt}
"""

    example_messages = [
        dict(
            role="user",
            content="Change get_factorial() to use math.factorial",
        ),
        dict(
            role="assistant",
            content="""<action_plan>
1. Import math in `mathweb/flask/app.py`.
2. Remove custom factorial() and update get_factorial() to use math.factorial.
Scope: Localized edits.
</action_plan>

mathweb/flask/app.py
{fence[0]}python
<<<<<<< SEARCH
import os
from flask import Flask
=======
import os
import math
from flask import Flask
>>>>>>> REPLACE
{fence[1]}

mathweb/flask/app.py
{fence[0]}python
<<<<<<< SEARCH
def factorial(n):
    "compute factorial"

    if n == 0:
        return 1
    else:
        return n * factorial(n-1)

=======
>>>>>>> REPLACE
{fence[1]}

mathweb/flask/app.py
{fence[0]}python
<<<<<<< SEARCH
def get_factorial(n):
    # Validates input first
    return str(factorial(n))
=======
def get_factorial(n):
    # Validates input first
    return str(math.factorial(n))
>>>>>>> REPLACE
{fence[1]}
""",
        )
    ]

    system_reminder = """<search_replace_rules>
MANDATORY FORMAT:
1. FULL FILE PATH: Alone on a line.
2. OPENING FENCE: {fence[0]}code_language
3. SEARCH HEADER: <<<<<<< SEARCH
4. SEARCH CONTENT: Exact match. Include container markup/escapes for JSON/XML.
5. DIVIDER: =======
6. REPLACE CONTENT: The updated code.
7. REPLACE FOOTER: >>>>>>> REPLACE
8. CLOSING FENCE: {fence[1]}

<surgical_precision_guidelines>
- Include ONLY modifications plus 2-4 lines of context for uniqueness.
- MOVING CODE: Use 2 blocks (1 delete, 1 insert).
- NEW FILES: SEARCH section MUST be empty.
- UNIQUE MATCHING: Include enough lines in SEARCH to uniquely match the target.
</surgical_precision_guidelines>

{quad_backtick_reminder}
</search_replace_rules>

<shell_command_protocol>
{rename_with_shell}
{go_ahead_tip}
</shell_command_protocol>

<critical_boundary>
STRICTLY FORBIDDEN: Code outside SEARCH/REPLACE blocks.
REQUIRED: Shell commands in `bash` block at the ABSOLUTE end.
{final_reminders}
{shell_cmd_reminder}
</critical_boundary>
"""

    rename_with_shell = "RENAME RULE: To rename files, use shell commands in the final bash block.\n"
    go_ahead_tip = "APPROVAL RULE: If user says 'ok', 'go ahead', 'go on', or 'do that', it means keep working on the previous task if it's not finished.\n"

    shell_cmd_prompt = shell.shell_cmd_prompt
    no_shell_cmd_prompt = shell.no_shell_cmd_prompt
    shell_cmd_reminder = shell.shell_cmd_reminder