┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Phase 1: Planning & test_todo.md Generation                                                                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛


Target Module Analysis

Module: aider/tcpe_engine.py Complexity: HIGH (10 methods, AST parsing, file I/O, complex logic) Sharding Required: YES (will
exceed 300 lines)


Mirror Architecture Paths

 • [x] tests/basic/test_tcpe_engine_init.py - Initialization and logging tests
 • [x] tests/basic/test_tcpe_engine_fqn.py - FQN extraction tests
 • [x] tests/basic/test_tcpe_engine_symbols.py - Symbol frequency extraction tests
 • [x] tests/basic/test_tcpe_engine_anti_doublon.py - Anti-doublon safety checks
 • [x] tests/basic/test_tcpe_engine_lifecycle.py - Failed block tracking and lifecycle
 • [x] tests/basic/test_tcpe_engine_scrub.py - Message scrubbing tests
 • [x] tests/basic/conftest.py - Shared fixtures for TCPEngine tests


Logic Analysis Blueprint - ALL SCENARIOS COMPLETED

tests/basic/conftest.py

 • [x] Fixture: mock_io - Mock InputOutput with tool_warning method
 • [x] Fixture: tcpe_engine - TCPEngine instance with mock_io
 • [x] Fixture: tmp_tcpe_dir - Temporary directory for TCPE logs

tests/basic/test_tcpe_engine_init.py

 • [x] Scenario: Initialize TCPEngine with valid IO
 • [x] Scenario: _log creates directory and writes JSON
 • [x] Scenario: _log handles exception silently
 • [x] Scenario: Initialize TCPEngine stores io reference (Phase 3 addition)

tests/basic/test_tcpe_engine_fqn.py

 • [x] Scenario: _get_node_fqn with simple identifier
 • [x] Scenario: _get_node_fqn with class method
 • [x] Scenario: _get_node_fqn with nested scopes

tests/basic/test_tcpe_engine_symbols.py

 • [x] Scenario: _get_symbols_with_frequencies with empty content
 • [x] Scenario: _get_symbols_with_frequencies with Python code
 • [x] Scenario: _get_symbols_with_frequencies with C++ overloads (Phase 3 addition)
 • [x] Scenario: _get_symbols_with_frequencies handles parse error

tests/basic/test_tcpe_engine_anti_doublon.py

 • [x] Scenario: check_anti_doublon allows unique symbols
 • [x] Scenario: check_anti_doublon blocks duplicate symbols
 • [x] Scenario: check_anti_doublon handles syntax errors
 • [x] Scenario: check_anti_doublon handles unknown language
 • [x] Scenario: check_anti_doublon handles missing query

tests/basic/test_tcpe_engine_lifecycle.py

 • [x] Scenario: track_failed_block adds to failed_blocks
 • [x] Scenario: increment_turn_and_timeout increments counter
 • [x] Scenario: increment_turn_and_timeout removes abandoned blocks
 • [x] Scenario: process_successful_edit resolves fuzzy match
 • [x] Scenario: process_successful_edit ignores low similarity

tests/basic/test_tcpe_engine_scrub.py

 • [x] Scenario: scrub_message with exact block match
 • [x] Scenario: scrub_message with fuzzy block match (Phase 3 addition)
 • [x] Scenario: scrub_message with no blocks
 • [x] Scenario: scrub_message with modified symbols
 • [x] Scenario: scrub_message with empty content
