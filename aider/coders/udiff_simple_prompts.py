#updated
from .udiff_prompts import UnifiedDiffPrompts


class UnifiedDiffSimplePrompts(UnifiedDiffPrompts):
    """
    Prompts for the UnifiedDiffSimpleCoder.
    Inherits from UnifiedDiffPrompts and can override specific prompts
    if a simpler wording is desired for this edit format.
    """

    example_messages = []

    system_reminder = """<diff_format_rules>
MANDATORY FORMAT: Exact unified diffs that `diff -U0` would produce.

1. DELETIONS: Mark ALL removed or changed lines with `-`.
2. ADDITIONS: Mark ALL new or modified lines with `+`.
3. NEW FILES: Header must be `--- /dev/null` to `+++ path/to/new/file.ext`.
</diff_format_rules>

<critical_system_boundary>
WARNING: Precision is absolute. Think carefully and make sure you include and mark ALL lines that need to be removed or changed.
DO NOT leave out any lines or the diff patch will fail to apply cleanly against the current contents of the file.
Missing a single `-` or `+` line is a system failure.
{final_reminders}
</critical_system_boundary>
"""  # noqa
