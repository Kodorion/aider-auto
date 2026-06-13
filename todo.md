# MASTER DIRECTIVE: TCPEngine Activation & Integration

**Role:** Expert Python Architect & Aider Core Contributor
**Objective:** Activate the dormant TCPEngine by wiring its orthogonal safety and summarization features into the active Aider edit workflow. Establish a robust test suite to prevent regression.

**Critical Architectural Constraint:** 
Do NOT modify base_coder.py's apply_edits stub. base_coder.py only contains stubs; the actual execution logic lives in subclasses (e.g., aider/coders/editblock_coder.py). All edit-application hooks must be placed in the concrete subclass where flexible_search_and_replace is actually executed.

---

## Progress Tracking via todo.md

You must maintain a `todo.md` file in the root directory to track your progress cleanly. 
Before starting any phase, create or update `todo.md` with the following structure using standard markdown checkboxes:

```markdown
# TCPEngine Integration Progress

## Phase 1: Context Gathering & Discovery
- [x] Read subclass apply_edits implementation.
- [x] Locate flexible_search_and_replace loop.
- [x] Identify text variables (original, search, replace, new).
- [x] Confirm self.tcpe location.

## Phase 2: Core Integration (Wiring the Clutch)
- [x] Inject Hook 1: The Failure Trap.
- [x] Inject Hook 2: The AST Guardian.
- [x] Inject Hook 3: The Success Resolver.

## Phase 3: Context Compression
- [x] Inject Hook 4: Semantic Summarization.

## Phase 4: Feature Gating & Production Safety
- [x] Implement Feature Gating.
- [x] Implement Fail-Safe Error Handling.

## Phase 5: Test Suite Creation
- [ ] Output summary of modified files and line numbers.
- [ ] HARD STOP: Ask user for 'skill unit test v2'.
```

Update this file by changing `- [ ]` to `- [x]` as you complete each step.

---

## Phase 1: Context Gathering & Discovery

Before writing code, you must map the exact execution layer.
1. Read `aider/coders/editblock_coder.py` (or the active subclass handling `apply_edits`).
2. Locate the exact loop where `flexible_search_and_replace` (from `search_replace.py`) is called.
3. Identify the variables holding `original_text` (or `original_content`), `search_text`, `replace_text`, and the resulting `new_text` (proposed content).
4. Confirm the location of `self.tcpe` (inherited from `base_coder.py`).

---

## Phase 2: Core Integration (Wiring the Clutch)

Modify the subclass's `apply_edits` method to inject the following 3 TCPEngine hooks.

### Hook 1: The Failure Trap (Phase 3)
**Location:** Immediately after `flexible_search_and_replace` returns `None` or fails to find a match (usually inside an `except` block or a `if not new_text:` check).
**Action:**
```python
self.tcpe.track_failed_block(rel_fname, replace_text)
```

### Hook 2: The AST Guardian (Phase 4 - Pre-Write Safety Net)
**Location:** Immediately after `flexible_search_and_replace` successfully returns `new_text`, but BEFORE `self.io.write_text(abs_fname, new_text)` is called.
**Action:**
```python
is_safe, error_msg = self.tcpe.check_anti_doublon(new_text, rel_fname, original_content)
if not is_safe:
    self.tcpe.track_failed_block(rel_fname, replace_text)
    self.io.tool_error(error_msg)
    continue
```

### Hook 3: The Success Resolver (Phase 3)
**Location:** Immediately after `self.io.write_text(abs_fname, new_text)` succeeds.
**Action:**
```python
self.tcpe.process_successful_edit(rel_fname, replace_text)
```

---

## Phase 3: Context Compression (Message Scrubbing)

Prevent context bloat by compressing successful SEARCH/REPLACE blocks in the chat history.

### Hook 4: Semantic Summarization (Phase 1 & 2)
**Location:** In the subclass's `apply_edits` method, right after a successful write (alongside Hook 3).
**Action:**
```python
modified_symbols = self.tcpe.extract_modified_symbols(rel_fname, original_content, new_text)
for msg in reversed(self.cur_messages):
    if msg.get("role") == "assistant" and rel_fname in msg.get("content", ""):
        msg["content"] = self.tcpe.scrub_message(
            msg["content"], rel_fname, modified_symbols, original_content, new_text
        )
        break
```

---

## Phase 4: Feature Gating & Production Safety

Tree-Sitter AST parsing is computationally expensive. To respect the decoupled/opt-in architecture and prevent production crashes:

1. **Feature Gating:** Wrap the Phase 2 and Phase 3 hooks in a conditional check. Gate this behind a CLI flag (e.g., `--enable-tcpe`), a model capability check, or an environment variable.
```python
if getattr(self, 'tcpe_enabled', False):
    # Execute Hooks 1, 2, 3, and 4
```

2. **Fail-Safe Error Handling:** Wrap all `self.tcpe.*` calls in `try/except Exception` blocks. If the TCPEngine crashes (e.g., Tree-Sitter fails on a weird file extension), log the error via `self.io.tool_warning()` and allow the edit to proceed safely. The guardian must never crash the main Aider edit loop.

---

## Phase 5: Test Suite Creation (HARD STOP)

**CRITICAL INSTRUCTION:**
You have now completed the architectural integration. DO NOT generate the test suite yet.

To ensure the highest quality testing standards, you must stop your execution here.
1. Update your `todo.md` to mark Phases 1-4 as complete.
2. Output a brief summary of the files modified and the exact line numbers where the hooks were placed.
3. Explicitly ask the human user: "Integration complete. Please provide the 'skill unit test v2' prompt/instructions so I can generate the regression test suite."
4. Wait for the human's response before proceeding to write any test files.

---

## Execution Rules for the Coding Agent

1. **Read-Only First:** Use file reading to map the exact subclass implementations of `apply_edits` before proposing any SEARCH/REPLACE blocks.
2. **Surgical Precision:** Do not rewrite entire methods. Use precise SEARCH/REPLACE blocks to inject the 4 hooks into the subclass.
3. **No Base Class Modification:** Do not touch `base_coder.py`'s `apply_edits` stub.
4. **Acknowledge:** Acknowledge this directive, create the initial `todo.md`, locate the subclasses, and begin Phase 1.
