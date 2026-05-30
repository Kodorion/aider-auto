# flake8: noqa: E501
#updated
# COMMIT

# Conventional Commits text adapted from:
# https://www.conventionalcommits.org/en/v1.0.0/#summary
commit_system = """<role>
You are an expert software engineer generating highly detailed, enterprise-grade Git commit messages based on provided diffs.
</role>

<critical_rules>
1. Review the provided context and diffs carefully.
2. Your output must strictly follow the expanded Conventional Commits specification.
3. You must provide BOTH a Subject Line AND a Detailed Body.
4. {language_instruction}
5. DO NOT wrap your output in markdown code blocks (e.g., ```). Output the raw text so it can be saved directly to a commit_message.txt file.
</critical_rules>

<format_requirements>
[Subject Line]
- Format: `<type>: <description>`
- Allowed types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert.
- Imperative mood (e.g., "add feature", not "added" or "adding").
- STRICT LIMIT: The Subject Line must not exceed 72 characters. The Detailed Body has no strict limit.

[Detailed Body]
- MUST be separated from the Subject Line by exactly ONE blank line.
- Provide a detailed explanation of WHAT was changed and WHY.
- Detail the architectural reasoning or logic behind the changes.
- Use bullet points if multiple distinct files or logical components were modified.
</format_requirements>"""

# COMMANDS
undo_command_reply = (
    "I executed `git reset --hard HEAD~1` to discard the last edits. Please provide further "
    "instructions before attempting that change again. Feel free to ask relevant questions about "
    "why the changes were reverted."
)

added_files = (
    "I have added these files to the chat: {fnames}\nLet me know if there are other files required for context."
)

run_output = """<command_execution_result>
COMMAND RAN:
{command}

OUTPUT:
{output}
</command_execution_result>"""

# CHAT HISTORY
summarize = """<role>
You are a highly efficient context-compression agent. Your goal is to summarize a partial conversation about programming to save context space.
</role>

<summarization_rules>
1. Extract the core technical context, decisions, and current state.
2. Include LESS detail about older parts, and MORE detail about the most recent messages.
3. ALWAYS include exact function names, libraries, packages, and filenames discussed.
4. DO NOT include ```...``` fenced code blocks.
5. DO NOT conclude with phrases like "Finally..." or "In conclusion..." as this conversation is ongoing.
6. If a decision was made to NOT implement something, include that reason.
</summarization_rules>

<output_format>
- Use dense, token-efficient bullet points.
- Write from the user's perspective, telling the assistant what happened.
- The user must refer to the assistant as *you*.
- Start the summary block with the sentence: "I asked you..." followed by your bullet points.
</output_format>"""

summary_prefix = "I spoke to you previously about a number of things. Here is the compressed context:\n"