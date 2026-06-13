import os
import json
import datetime
import re
from difflib import SequenceMatcher
from pathlib import Path
from tree_sitter import Query
from grep_ast.tsl import get_language, get_parser
from grep_ast import filename_to_lang
from aider.repomap import get_doublon_query

class TCPEngine:
    def __init__(self, io):
        self.io = io
        self.failed_blocks = []
        self.tcpe_log_path = ".tcpe_logs"

    def _log(self, event, data):
        """Log TCPE diagnostic events to disk silently."""
        try:
            if not os.path.exists(self.tcpe_log_path):
                os.makedirs(self.tcpe_log_path)
            log_file = os.path.join(self.tcpe_log_path, f"tcpe_{datetime.datetime.now().strftime('%Y%m%d')}.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({"time": datetime.datetime.now().isoformat(), "event": event, "data": data}) + "\n")
        except Exception:
            pass

    def _get_node_fqn(self, node):
        """
        Traverse upwards from the identifier node in the Tree-Sitter AST
        to build a Fully Qualified Name (FQN). This scopes methods to their 
        respective classes or parent scopes, preventing false-positive duplicate flags.
        """
        path = []
        curr = node.parent
        while curr:
            # Look for a field child labeled 'name' first
            name_child = curr.child_by_field_name('name')
            if name_child:
                path.append(name_child.text.decode('utf-8', errors='ignore'))
            else:
                # Fallback: check class/function structures if 'name' field is absent
                if curr.type in ('class_definition', 'class_declaration', 'function_definition', 'struct_specifier', 'impl_item', 'trait_item', 'module'):
                    for child in curr.children:
                        if child.type in ('identifier', 'type_identifier'):
                            path.append(child.text.decode('utf-8', errors='ignore'))
                            break
            curr = curr.parent
        
        path.reverse()
        path.append(node.text.decode('utf-8', errors='ignore'))
        return ".".join(path)

    def _get_symbols_with_frequencies(self, content, filename, lang, query_scm):
        """Helper to extract symbols and their frequency counts from code content."""
        if not content:
            return {}
        try:
            parser = get_parser(lang)
            tree = parser.parse(bytes(content, "utf-8"))
            language = get_language(lang)
            query = Query(language, query_scm)

            if hasattr(query, "captures"):
                captures = query.captures(tree.root_node)
            else:
                from tree_sitter import QueryCursor
                cursor = QueryCursor(query)
                captures = cursor.captures(tree.root_node)
        except Exception as e:
            self._log("get_symbols_error", {"filename": filename, "error": str(e)})
            return {}

        nodes_by_tag = captures
        if isinstance(captures, list):
            nodes_by_tag = {}
            for node, tag in captures:
                if tag not in nodes_by_tag:
                    nodes_by_tag[tag] = []
                nodes_by_tag[tag].append(node)

        counts = {}
        # C++, Rust, and Dart function overloads require signature uniqueness (Name + Params)
        if lang in ['cpp', 'rust', 'dart']:
            parents = {}
            for tag, nodes in nodes_by_tag.items():
                for node in nodes:
                    parent_id = node.parent.id if node.parent else id(node)
                    if parent_id not in parents:
                        parents[parent_id] = {}
                    # Store the node, not just the text
                    parents[parent_id][tag] = node
            for parent_id, tags in parents.items():
                if 'name' in tags:
                    # Use FQN on the original name node
                    name_node = tags['name']
                    # --- START: Visibility check for Rust/C++/Dart ---
                    func_node = name_node.parent
                    is_pub = False
                    if func_node:
                        # Check for 'pub' keyword or visibility modifier
                        for child in func_node.children:
                            if child.type == 'pub' or (child.type == 'visibility_modifier' and child.text == b'pub'):
                                is_pub = True
                                break
                    # Skip private functions entirely (they won't be counted)
                    if not is_pub:
                        continue
                    # --- END: Visibility check ---
                    full_name = self._get_node_fqn(name_node)
                    params = tags.get('params')
                    signature = full_name + (params.text.decode('utf-8', errors='ignore') if params else '')
                    counts[signature] = counts.get(signature, 0) + 1
        else:
            # Proper FQN Scope checking for Python, Java, JavaScript, and other languages
            for tag, nodes in nodes_by_tag.items():
                if tag == 'name':
                    for node in nodes:
                        symbol = self._get_node_fqn(node)
                        counts[symbol] = counts.get(symbol, 0) + 1
        return counts

    def check_anti_doublon(self, proposed_content, filename, original_content=None):
        """Phase 4: Polyglot Structural Integrity Guard (Delta Frequency Check)"""
        lang = filename_to_lang(filename)
        if not lang:
            return True, None
            
        query_scm = get_doublon_query(lang)
        if not query_scm:
            return True, None

        # Syntax check on the proposed content first to avoid masking duplicates
        try:
            parser = get_parser(lang)
            tree = parser.parse(bytes(proposed_content, "utf-8"))
        except Exception as e:
            self._log("anti_doublon_parse_error", {"filename": filename, "error": str(e)})
            return True, None

        if tree.root_node.has_error:
            self._log("anti_doublon_syntax_error", {"filename": filename})
            return False, f"[SYSTEM LOG: Edit aborted. Syntax error detected in the proposed edit for {Path(filename).name}. Aborting write to prevent syntax errors from masking duplicate declarations.]"

        # Determine the original content state safely
        if original_content is None:
            if os.path.exists(filename):
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        original_content = f.read()
                except Exception:
                    original_content = ""
            else:
                original_content = ""

        # Count occurrences in both original and proposed states
        old_counts = self._get_symbols_with_frequencies(original_content, filename, lang, query_scm)
        new_counts = self._get_symbols_with_frequencies(proposed_content, filename, lang, query_scm)

        # Delta Check: Block edit only if symbol count increases AND new count is duplicate (> 1)
        for symbol, new_count in new_counts.items():
            old_count = old_counts.get(symbol, 0)
            if new_count > old_count and new_count > 1:
                self._log("anti_doublon_blocked", {
                    "filename": filename, 
                    "symbol": symbol, 
                    "old_count": old_count, 
                    "new_count": new_count
                })
                raw_name = symbol.split('.')[-1]
                return False, f"[SYSTEM LOG: Edit aborted, your SEARCH block didn't match the current file exactly, so no changes were made; file unchanged, no duplicate code introduced – please provide a corrected SEARCH/REPLACE block.]"

        return True, None

    def extract_modified_symbols(self, filename, original_content, new_content):
        """Phase 2: Extract structural changes to provide semantic summaries"""
        lang = filename_to_lang(filename)
        if not lang:
            return []
            
        query_scm = get_doublon_query(lang)
        if not query_scm:
            return []

        try:
            orig_symbols = set(self._get_symbols_with_frequencies(original_content, filename, lang, query_scm).keys())
            new_symbols = set(self._get_symbols_with_frequencies(new_content, filename, lang, query_scm).keys())
            modified = list(new_symbols - orig_symbols)
            return modified
        except Exception:
            return []

    def track_failed_block(self, filename, replace_text):
        """Phase 3: Keep track of failing blocks for scoped pruning"""
        self.failed_blocks.append({
            "file": filename,
            "replace": replace_text,
            "turns_unaddressed": 0
        })
        self._log("track_failed", {"filename": filename})

    def increment_turn_and_timeout(self, coder_messages):
        """Phase 3: Timeout logic for abandoned blocks"""
        surviving_blocks = []
        timeout_messages = []
        for block in self.failed_blocks:
            block["turns_unaddressed"] += 1
            if block["turns_unaddressed"] >= 3:
                self._log("abandoned_block", {"filename": block["file"]})
                timeout_messages.append(f"[SYSTEM LOG: Previous failed edit for {Path(block['file']).name} abandoned and purged from memory.]")
            else:
                surviving_blocks.append(block)

        self.failed_blocks = surviving_blocks

        if timeout_messages and coder_messages:
            for msg in timeout_messages:
                coder_messages.append({"role": "assistant", "content": msg})

    def process_successful_edit(self, filename, replace_text):
        """Phase 3: Fuzzy Intent-Scoped State Management"""
        resolved_indices = []
        for i, block in enumerate(self.failed_blocks):
            if block["file"] == filename:
                sim = SequenceMatcher(None, block["replace"], replace_text).ratio()
                if sim > 0.75:
                    resolved_indices.append(i)
                    self._log("fuzzy_resolved", {"filename": filename, "similarity": sim})

        for i in reversed(resolved_indices):
            del self.failed_blocks[i]

    def scrub_message(self, message_content, filename, modified_symbols, original, updated):
        """Phase 1 & 2: Regex Pruning and Deterministic Summarization"""
        if not message_content:
            return message_content

        if modified_symbols:
            top_symbols = [sym.split('.')[-1] for sym in modified_symbols[:3]]
            more_count = max(0, len(modified_symbols) - 3)
            sym_str = ", ".join(top_symbols)
            if more_count > 0:
                sym_str += f", and {more_count} sub-elements"
            summary = f"[SYSTEM LOG: Edits applied to {Path(filename).name}. Modified symbols: {sym_str}. Raw context pruned.]"
        else:
            summary = f"[SYSTEM LOG: Edits applied to {Path(filename).name}. Raw context pruned.]"

        # Attempt exact structural match
        block = f"<<<<<<< SEARCH\n{original}=======\n{updated}>>>>>>> REPLACE"
        if block in message_content:
            return message_content.replace(block, f"\n{summary}\n")
            
        # Fallback 1: Fuzzy block match to target the exact REPLACE segment
        blocks = re.findall(r"(<<<<<<< SEARCH.*?>>>>>>> REPLACE)", message_content, re.DOTALL)
        for b in blocks:
            if updated.strip() in b:
                return message_content.replace(b, f"\n{summary}\n")
                
        # Fallback 2: Replace first instance found in message
        pattern = re.compile(r"<<<<<<< SEARCH.*?>>>>>>> REPLACE", re.DOTALL)
        return pattern.sub(f"\n{summary}\n", message_content, count=1)
