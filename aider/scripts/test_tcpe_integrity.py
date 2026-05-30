import sys
from pathlib import Path

# Add root directory to sys.path so we can import aider
sys.path.insert(0, str(Path(__file__).parent.parent))

from aider.tcpe_engine import TCPEngine

class MockIO:
    def tool_output(self, *args, **kwargs): pass
    def tool_warning(self, *args, **kwargs): pass
    def tool_error(self, *args, **kwargs): pass

# --- PHASE 4: ANTI-DOUBLON TESTS ---

def test_python_doublon():
    engine = TCPEngine(MockIO())
    
    content_invalid = "def process():\n    pass\ndef process():\n    return True\n"
    is_safe, err = engine.check_anti_doublon(content_invalid, "test.py")
    assert not is_safe, "Failed to catch Python doublon"
    
    content_valid = "def process():\n    pass\nclass Process:\n    pass\n"
    is_safe, err = engine.check_anti_doublon(content_valid, "test.py")
    assert is_safe, "Falsely flagged valid Python code"
    print("✓ Python structural integrity")

def test_cpp_doublon():
    engine = TCPEngine(MockIO())
    content_valid = "void print(int v) {}\nvoid print(std::string v) {}\n"
    is_safe, _ = engine.check_anti_doublon(content_valid, "test.cpp")
    assert is_safe, "Falsely flagged valid C++ function overload"

    content_invalid = "void print(int v) {}\nvoid print(int v) { return; }\n"
    is_safe, _ = engine.check_anti_doublon(content_invalid, "test.cpp")
    assert not is_safe, "Failed to catch C++ signature doublon"
    print("✓ C++ structural integrity (Overloads)")

def test_typescript_html_doublon():
    engine = TCPEngine(MockIO())
    
    ts_invalid = "class User {}\nclass User { constructor() {} }\n"
    is_safe, _ = engine.check_anti_doublon(ts_invalid, "test.ts")
    assert not is_safe, "Failed to catch TypeScript class doublon"

    html_invalid = "<div id='main'></div>\n<span id='main'></span>\n"
    is_safe, _ = engine.check_anti_doublon(html_invalid, "test.html")
    assert not is_safe, "Failed to catch HTML ID doublon"
    print("✓ TypeScript & HTML structural integrity")

def test_syntax_masking():
    engine = TCPEngine(MockIO())
    content_syntax_err = "def bad():\n    if True\n        pass\ndef bad():\n    pass\n"
    is_safe, err = engine.check_anti_doublon(content_syntax_err, "test.py")
    assert not is_safe and "Syntax error" in err, "Failed to abort on syntax error"
    print("✓ Syntax-Error Masking")

# --- PHASES 1-3: MEMORY HYGIENE TESTS ---

def test_fuzzy_resolution():
    engine = TCPEngine(MockIO())
    
    # 1. Track a failed block
    engine.track_failed_block("app.py", "def init():\n    start_server(port=8080)\n")
    assert len(engine.failed_blocks) == 1
    
    # 2. Process a successful edit that is very similar (fixed a typo/port)
    engine.process_successful_edit("app.py", "def init():\n    start_server(port=9000)\n")
    
    # 3. Assert the fuzzy matcher recognized it and purged the failed block
    assert len(engine.failed_blocks) == 0, "Fuzzy matcher failed to clear resolved block"
    print("✓ Fuzzy Intent Resolution")

def test_timeout_abandonment():
    engine = TCPEngine(MockIO())
    
    engine.track_failed_block("config.json", '{"key": "val"}')
    
    # Seed with a dummy message to simulate Aider's cur_messages which is never empty at this stage
    messages = [{"role": "user", "content": "Dummy turn"}]
    
    # Simulate 3 turns of the agent doing other things
    engine.increment_turn_and_timeout(messages)
    engine.increment_turn_and_timeout(messages)
    engine.increment_turn_and_timeout(messages)
    
    assert len(engine.failed_blocks) == 0, "Failed to purge abandoned block after 3 turns"
    assert len(messages) == 2, "Failed to generate system timeout message"
    print("✓ Abandonment Timeout")

def test_regex_scrubbing():
    engine = TCPEngine(MockIO())
    
    chat_message = """Here is the fix:
<<<<<<< SEARCH
old_code()
=======
new_code()
>>>>>>> REPLACE
And now I will wait."""

    scrubbed = engine.scrub_message(chat_message, "main.py", ["new_code"], "old_code()\n", "new_code()\n")
    
    assert "<<<<<<< SEARCH" not in scrubbed, "Failed to scrub diff fences"
    assert "Modified symbols: new_code" in scrubbed, "Failed to inject deterministic summary"
    assert "Here is the fix:" in scrubbed, "Erased Chain of Thought"
    print("✓ Regex Pruning & Summarization")

if __name__ == "__main__":
    print("Running TCPE v3 Unit Tests...\n")
    test_python_doublon()
    test_cpp_doublon()
    test_typescript_html_doublon()
    test_syntax_masking()
    test_fuzzy_resolution()
    test_timeout_abandonment()
    test_regex_scrubbing()
    print("\nAll TCPE Integrity & Hygiene Tests Passed!")