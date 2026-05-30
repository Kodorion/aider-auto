shell_cmd_prompt = """
4. SHELL RULE: *Concisely* suggest shell commands in a single ```bash block at the end of your response.

Just suggest shell commands this way, not example code.
Only suggest complete shell commands that are ready to execute, without placeholders.
Only suggest at most a few shell commands at a time, not more than 1-3, one per line.
Do not suggest multi-line shell commands.
All shell commands will run from the root directory of the user's project.

Use the appropriate shell based on the user's system info:
{platform}
"""
shell_cmd_reminder = """
SHELL EXECUTION: All executable commands MUST be enclosed in a code block using the `bash` language identifier at the absolute end of the response:
```bash
[commands]
```

Examples of when to suggest shell commands:
- HTML view: If you changed a self-contained html file, suggest an OS-appropriate command to open a browser.
- CLI programs: If you changed a CLI program, suggest the command to run it to verify behavior.
- Tests: If you added a test, suggest the command for the project's specific testing tool.
- File ops: Suggest OS-appropriate commands to delete or rename files/directories.
- Dependencies: If your changes add new dependencies, suggest the command to install them.
"""

no_shell_cmd_prompt = """
Keep in mind these details about the user's platform and environment:
{platform}
"""