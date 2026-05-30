class CoderPrompts:
    system_reminder = ""

    files_content_gpt_edits = "I committed the changes with git hash {hash} & commit msg: {message}"
    files_content_gpt_edits_no_repo = "I updated the files."
    files_content_gpt_no_edits = "I didn't see any properly formatted edits in your reply?!"
    files_content_local_edits = "I edited the files myself."

    lazy_prompt = """<rules>
- NEVER use placeholders or elisions (e.g., `# ... existing code ...`).
- OUTPUT COMPLETE, EXECUTABLE CODE for all modifications.
</rules>"""

    overeager_prompt = """<scope_constraints>
- Fulfill request EXACTLY, then STOP.
- FORBIDDEN: Unrelated refactoring, formatting, or modifying unlisted files.
- ASK PERMISSION before modifying unlisted dependencies.
</scope_constraints>"""

    example_messages = []

    files_content_prefix = """I have *added these files to the chat* so you can go ahead and edit them.

*LITERALISM RULE: Trust this message as the absolute, Ground Truth contents of these files!*
*LITERALISM RULE: If your reasoning contradicts the code you see below, your reasoning is wrong. Do not hypothesize that the files are "different".*
Any other messages in the chat may contain outdated versions of the files' contents.
"""

    files_content_assistant_reply = "Ok, any changes I propose will be to those files."
    files_no_full_files = "I am not sharing any files that you can edit yet."

    files_no_full_files_with_repo_map = """<edit_protocol>
STATE: Missing file contents. DO NOT write code from repo map.
1. Identify files that MUST be modified to solve the request and ask for them with <file_request> protocol.
2. FORBIDDEN: Do not request files for context/reference only.
3. OUTPUT ONLY the list of files to be EDITED.
4. STOP and WAIT for user to provide contents.
</edit_protocol>"""

    files_no_full_files_with_repo_map_reply = (
        "Ok, based on your requests I will suggest which files need to be edited and then"
        " stop and wait for your approval."
    )

    repo_content_prefix = """<repo_map_context>
WARNING: Summaries ONLY. Treat as READ-ONLY.
- DO NOT hallucinate internal contents, variables, or functions.
- To edit or interface or see any file, IF external files not in chat are needed: You MUST use the following exact output format, stop, and wait for approval:
<file_request>
`path\to\file1.ext`
`path\to\file2.ext`
</file_request>

</repo_map_context>
"""

    read_only_files_prefix = """Here are some READ ONLY files, provided for your reference.
Do not edit these files!
"""

    # Placeholders for specialization in child classes
    shell_cmd_prompt = ""
    shell_cmd_reminder = ""
    no_shell_cmd_prompt = ""
    no_shell_cmd_reminder = ""
    rename_with_shell = ""
    go_ahead_tip = ""