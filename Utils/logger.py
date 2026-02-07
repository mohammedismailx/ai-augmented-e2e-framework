"""
Centralized Logger Module for AI-Augmented E2E Framework
Handles all logging with proper Windows encoding support (no Unicode/emoji issues)
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any


class FrameworkLogger:
    """
    Centralized logger that handles console and file logging with proper encoding.
    All print statements across the framework should use this logger.
    """

    # Class-level file handle for persistent file logging
    _file_handle = None
    _log_file_path = None
    _session_active = False

    def __init__(self, log_file: Optional[str] = None, console_output: bool = True):
        """
        Initialize the logger.

        Args:
            log_file: Path to log file. If None, only console output is used.
            console_output: Whether to also print to console.
        """
        self.console_output = console_output
        self.log_file = log_file

    # =========================================================================
    # STATIC METHODS - Can be called without instantiation
    # =========================================================================

    @staticmethod
    def safe_print(message: str):
        """Print message safely, handling Windows encoding issues."""
        try:
            print(message)
        except UnicodeEncodeError:
            # Fallback: encode with errors replaced
            safe_msg = message.encode("ascii", errors="replace").decode("ascii")
            print(safe_msg)

    @staticmethod
    def info(message: str):
        """Log an info message."""
        FrameworkLogger.safe_print(f"[INFO] {message}")

    @staticmethod
    def ok(message: str):
        """Log a success message."""
        FrameworkLogger.safe_print(f"[OK] {message}")

    @staticmethod
    def warning(message: str):
        """Log a warning message."""
        FrameworkLogger.safe_print(f"[WARNING] {message}")

    @staticmethod
    def error(message: str):
        """Log an error message."""
        FrameworkLogger.safe_print(f"[ERROR] {message}")

    @staticmethod
    def fail(message: str):
        """Log a failure message."""
        FrameworkLogger.safe_print(f"[FAIL] {message}")

    @staticmethod
    def debug(message: str):
        """Log a debug message."""
        FrameworkLogger.safe_print(f"[DEBUG] {message}")

    @staticmethod
    def step(step_num: int, message: str):
        """Log a step message."""
        FrameworkLogger.safe_print(f"[STEP {step_num}] {message}")

    @staticmethod
    def section(title: str):
        """Log a section header."""
        FrameworkLogger.safe_print(f"\n{'='*80}")
        FrameworkLogger.safe_print(title)
        FrameworkLogger.safe_print(f"{'='*80}")

    @staticmethod
    def subsection(title: str):
        """Log a subsection header."""
        FrameworkLogger.safe_print(f"\n{'-'*60}")
        FrameworkLogger.safe_print(title)
        FrameworkLogger.safe_print(f"{'-'*60}")

    @staticmethod
    def separator():
        """Log a separator line."""
        FrameworkLogger.safe_print("_" * 80)

    @staticmethod
    def blank():
        """Log a blank line."""
        FrameworkLogger.safe_print("")

    @staticmethod
    def tree_item(message: str, last: bool = False):
        """Log a tree-style item (replaces box-drawing characters)."""
        prefix = "  +-- " if last else "  |-- "
        FrameworkLogger.safe_print(f"{prefix}{message}")

    @staticmethod
    def json_block(data: Any, title: Optional[str] = None, max_chars: int = 3000):
        """Log a JSON block with optional title."""
        if title:
            FrameworkLogger.safe_print(f"\n--- {title} ---")

        try:
            if isinstance(data, str):
                formatted = data
            else:
                formatted = json.dumps(data, indent=2)

            if len(formatted) > max_chars:
                FrameworkLogger.safe_print(formatted[:max_chars])
                FrameworkLogger.safe_print(
                    f"\n... (truncated, {len(formatted) - max_chars} more chars)"
                )
            else:
                FrameworkLogger.safe_print(formatted)
        except Exception as e:
            FrameworkLogger.safe_print(f"(Could not format: {e})")

        if title:
            FrameworkLogger.safe_print(f"--- END {title} ---\n")

    @staticmethod
    def box(title: str, content: str, max_lines: int = 50):
        """Log content in a box format."""
        FrameworkLogger.safe_print(f"\n+{'-'*78}+")
        FrameworkLogger.safe_print(f"| {title:<76} |")
        FrameworkLogger.safe_print(f"+{'-'*78}+")

        lines = content.split("\n")
        for line in lines[:max_lines]:
            # Truncate long lines
            if len(line) > 76:
                line = line[:73] + "..."
            FrameworkLogger.safe_print(f"| {line:<76} |")

        if len(lines) > max_lines:
            FrameworkLogger.safe_print(
                f"| {'... (' + str(len(lines) - max_lines) + ' more lines)':<76} |"
            )

        FrameworkLogger.safe_print(f"+{'-'*78}+")

    @staticmethod
    def result(success: bool, message: str = ""):
        """Log a test result."""
        if success:
            FrameworkLogger.safe_print(f"\n{'='*80}")
            FrameworkLogger.safe_print(
                f"                         [OK] TEST PASSED [OK]"
            )
            if message:
                FrameworkLogger.safe_print(f"                         {message}")
            FrameworkLogger.safe_print(f"{'='*80}")
        else:
            FrameworkLogger.safe_print(f"\n{'='*80}")
            FrameworkLogger.safe_print(
                f"                         [FAIL] TEST FAILED [FAIL]"
            )
            if message:
                FrameworkLogger.safe_print(f"                         {message}")
            FrameworkLogger.safe_print(f"{'='*80}")


class IntentLogger:
    """
    Logger specifically for intent-based API/DB/UI execution.
    Logs to both console and file with proper formatting.
    Automatically reads test ID and title from builtins.CURRENT_TEST_INFO.
    """

    # Class-level log file paths
    API_LOG_FILE = "api_with_intent_logs.txt"
    DB_LOG_FILE = "db_with_intent_logs.txt"
    UI_LOG_FILE = "ui_with_intent_logs.txt"

    def __init__(self, log_file: str = None, test_type: str = "API"):
        """
        Initialize the intent logger.

        Args:
            log_file: Path to log file. If None, uses default based on test_type.
            test_type: Type of test - "API", "DB", or "UI"
        """
        self.test_type = test_type.upper()
        if log_file is None:
            if self.test_type == "DB":
                self.log_file = self.DB_LOG_FILE
            elif self.test_type == "UI":
                self.log_file = self.UI_LOG_FILE
            else:
                self.log_file = self.API_LOG_FILE
        else:
            self.log_file = log_file
        self.file_handle = None
        self.session_start = None
        self.test_id = None
        self.test_title = None

    def _get_test_info_from_builtins(self):
        """Get test ID and title from builtins.CURRENT_TEST_INFO if available."""
        import builtins

        test_info = getattr(builtins, "CURRENT_TEST_INFO", {})
        self.test_id = test_info.get("id", "UNKNOWN")
        self.test_title = test_info.get("title", "")
        return self.test_id, self.test_title

    def start_session(self, intent: str = None):
        """Start a new logging session with test ID from pytest markers."""
        self.session_start = datetime.now()

        # Get test info from builtins (set by pytest fixture)
        test_id, test_title = self._get_test_info_from_builtins()

        # Open file in append mode with explicit UTF-8 encoding (no BOM)
        # Using newline="" to prevent double line endings on Windows
        try:
            self.file_handle = open(
                self.log_file, "a", encoding="utf-8", errors="replace", newline="\n"
            )
        except Exception as e:
            FrameworkLogger.warning(f"Could not open log file: {e}")
            self.file_handle = None

        # Build header with test ID prominently displayed
        intent_line = f"Intent: {intent}" if intent else ""

        header = f"""

################################################################################
################################################################################
##                                                                            ##
##  NEW TEST EXECUTION: [{test_id}] {test_title:<43} ##
##                                                                            ##
################################################################################
################################################################################

================================================================================
                    INTENT-BASED {self.test_type} EXECUTION LOG
================================================================================
Test ID: {test_id}
Test Title: {test_title or 'N/A'}
Test Type: {self.test_type}
Session Start: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}
{intent_line}
================================================================================
"""
        self.log(header)

    def end_session(self):
        """End the logging session."""
        if self.session_start:
            duration = datetime.now() - self.session_start
            test_id = self.test_id or "UNKNOWN"
            test_title = self.test_title or ""
            footer = f"""
================================================================================
END OF TEST: [{test_id}] {test_title}
Session End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration.total_seconds():.2f} seconds
================================================================================

"""
            self.log(footer)

        if self.file_handle:
            try:
                self.file_handle.close()
            except:
                pass
            self.file_handle = None

    def log(self, message: str):
        """Log a message to both console and file."""
        # Console output (safe print)
        try:
            print(message)
        except UnicodeEncodeError:
            safe_msg = message.encode("ascii", errors="replace").decode("ascii")
            print(safe_msg)

        # File output
        if self.file_handle:
            try:
                self.file_handle.write(message + "\n")
                self.file_handle.flush()
            except Exception as e:
                pass  # Silently ignore file write errors

    def log_step_separator(self):
        """Log a step separator."""
        self.log("\n" + "_" * 80 + "\n")

    def log_section(self, title: str):
        """Log a section header."""
        self.log(f"\n{'='*80}")
        self.log(title)
        self.log(f"{'='*80}")

    def log_prompt(self, prompt: str):
        """Log a prompt sent to GitLab Duo."""
        self.log(f"\n{'-'*40} PROMPT TO GITLAB DUO {'-'*40}")

        if len(prompt) > 5000:
            self.log(prompt[:5000])
            self.log(f"\n... (truncated, {len(prompt) - 5000} more chars)")
        else:
            self.log(prompt)

        self.log(f"{'-'*80}\n")

    def log_ai_response(self, response: str):
        """Log an AI response from GitLab Duo."""
        self.log(f"\n{'-'*40} GITLAB DUO RESPONSE {'-'*40}")

        if len(response) > 5000:
            self.log(response[:5000])
            self.log(f"\n... (truncated, {len(response) - 5000} more chars)")
        else:
            self.log(response)

        self.log(f"{'-'*80}\n")

    def log_titled_block(self, title: str, content: str, max_chars: int = 3000):
        """Log a titled block of content."""
        self.log(f"\n--- {title} ---")

        if len(content) > max_chars:
            self.log(content[:max_chars])
            self.log(f"\n... (truncated, {len(content) - max_chars} more chars)")
        else:
            self.log(content)

        self.log(f"--- END {title} ---\n")

    def log_summary(self, summary_data: Dict[str, Any]):
        """Log an execution summary."""
        self.log(f"\n{'='*80}")
        self.log("                         EXECUTION SUMMARY")
        self.log(f"{'='*80}")

        for key, value in summary_data.items():
            value_str = str(value) if value is not None else "N/A"
            if len(value_str) > 60:
                value_str = value_str[:57] + "..."
            self.log(f"  {key}: {value_str}")

        self.log(f"{'='*80}\n")

    # =========================================================================
    # VERBOSE LOGGING METHODS FOR UI INTENT EXECUTION
    # =========================================================================

    def log_rag_retrieval(
        self,
        module: str,
        found: bool,
        status: str = None,
        action_key: str = None,
        match_score: float = None,
    ):
        """Log RAG retrieval attempt and result."""
        self.log(f"\n[RETRIEVE] Checking ChromaDB for module: {module}")

        if found and status == "[correct]":
            self.log(f"[RETRIEVE] Found [correct] action in ChromaDB")
            if action_key:
                self.log(f"[RETRIEVE] Action key: {action_key}")
            if match_score is not None:
                self.log(f"[RETRIEVE] Match score: {match_score:.3f}")
        else:
            self.log(f"[RETRIEVE] No [correct] action found - using live HTML")
            if status:
                self.log(f"[RETRIEVE] Previous status: {status}")

    def log_stored_metadata(self, metadata: dict):
        """Log full stored metadata from ChromaDB."""
        self.log(f"\n[RAG DATA] ─────────────────────────────────────────────")
        self.log(f"[RAG DATA] STORED METADATA FROM CHROMADB:")
        self.log(f"[RAG DATA]   action_key: {metadata.get('action_key', 'N/A')}")
        self.log(f"[RAG DATA]   intent: {metadata.get('intent', 'N/A')}")
        self.log(f"[RAG DATA]   action_type: {metadata.get('action_type', 'N/A')}")
        self.log(f"[RAG DATA]   locator: {metadata.get('locator', 'N/A')}")
        self.log(
            f"[RAG DATA]   playwright_code: {metadata.get('playwright_code', 'N/A')}"
        )
        self.log(f"[RAG DATA]   status: {metadata.get('status', 'N/A')}")
        self.log(f"[RAG DATA] ─────────────────────────────────────────────")

    def log_live_html_elements(
        self,
        elements: list,
        max_elements: int = 5,
        max_length: int = 200,
        is_retry: bool = False,
    ):
        """Log live HTML elements extracted from page."""
        tag = "[LIVE HTML RETRY]" if is_retry else "[LIVE HTML]"
        header = "ELEMENTS FOR RETRY:" if is_retry else "ELEMENTS SENT TO DUO:"

        self.log(f"\n{tag} ─────────────────────────────────────────────")
        self.log(f"{tag} {header}")

        for i, elem in enumerate(elements[:max_elements], 1):
            elem_display = elem[:max_length] + "..." if len(elem) > max_length else elem
            self.log(f"{tag}   {i}. {elem_display}")

        if len(elements) > max_elements:
            self.log(f"{tag}   ... and {len(elements) - max_elements} more elements")

        self.log(f"{tag} ─────────────────────────────────────────────")

    def log_duo_request(
        self, source: str, module: str, step_intent: str, step_type: str
    ):
        """Log the request being sent to GitLab Duo."""
        self.log(f"\n[DUO REQUEST] ═══════════════════════════════════════════════════")
        self.log(f"[DUO REQUEST] Source: {source}")
        self.log(f"[DUO REQUEST] Module: {module}")
        self.log(f"[DUO REQUEST] Step Intent: {step_intent}")
        self.log(f"[DUO REQUEST] Step Type: {step_type}")

    def log_duo_prompt(self, prompt: str, max_lines: int = 50):
        """Log the full prompt being sent to GitLab Duo."""
        self.log(f"\n[PROMPT] ─────────────────────────────────────────────")
        self.log(f"[PROMPT] PROMPT SENT TO GITLAB DUO:")

        prompt_lines = prompt.strip().split("\n")
        for line in prompt_lines[:max_lines]:
            self.log(f"[PROMPT] {line.strip()}")

        if len(prompt_lines) > max_lines:
            self.log(
                f"[PROMPT] ... (truncated, {len(prompt_lines) - max_lines} more lines)"
            )

        self.log(f"[PROMPT] ─────────────────────────────────────────────")

    def log_duo_response(self, response: dict, is_retry: bool = False):
        """Log full response from GitLab Duo."""
        import json

        tag = "[DUO RESPONSE RETRY]" if is_retry else "[DUO RESPONSE]"

        self.log(f"\n{tag} ═══════════════════════════════════════════════════")
        self.log(f"{tag} FULL RESPONSE FROM GITLAB DUO:")
        self.log(f"{tag}   action_key: {response.get('action_key', 'N/A')}")
        self.log(f"{tag}   intent: {response.get('intent', 'N/A')}")
        self.log(f"{tag}   action_type: {response.get('action_type', 'N/A')}")
        self.log(f"{tag}   locator: {response.get('locator', 'N/A')}")

        action_json = response.get("action_json", {})
        if isinstance(action_json, dict):
            self.log(f"{tag}   action_json: {json.dumps(action_json)}")
        else:
            self.log(f"{tag}   action_json: {action_json}")

        self.log(f"{tag}   playwright_code: {response.get('playwright_code', 'N/A')}")
        self.log(f"{tag} ═══════════════════════════════════════════════════")

    def log_store_action(
        self,
        module: str,
        action_key: str,
        status: str,
        locator: str = None,
        playwright_code: str = None,
        context: str = None,
    ):
        """Log action being stored in ChromaDB."""
        self.log(f"\n[STORE] ─────────────────────────────────────────────")

        if context:
            self.log(f"[STORE] {context}:")
        else:
            self.log(f"[STORE] STORING ACTION IN CHROMADB:")

        self.log(f"[STORE]   module: {module}")
        self.log(f"[STORE]   action_key: {action_key}")
        self.log(f"[STORE]   status: {status}")

        if locator:
            self.log(f"[STORE]   locator: {locator}")
        if playwright_code:
            self.log(f"[STORE]   playwright_code: {playwright_code}")

        self.log(f"[STORE] ─────────────────────────────────────────────")


# Convenience aliases
log = FrameworkLogger
logger = FrameworkLogger

# Pre-instantiated intent logger (can be used directly)
intent_logger = IntentLogger()
