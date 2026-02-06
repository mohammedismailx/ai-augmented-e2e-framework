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
    Logger specifically for intent-based API execution.
    Logs to both console and file with proper formatting.
    """

    def __init__(self, log_file: str = "api_with_intent_logs.txt"):
        """Initialize the intent logger with a log file."""
        self.log_file = log_file
        self.file_handle = None
        self.session_start = None

    def start_session(self, intent: str = None):
        """Start a new logging session."""
        self.session_start = datetime.now()

        # Open file in append mode with UTF-8 encoding
        try:
            self.file_handle = open(self.log_file, "a", encoding="utf-8")
        except Exception as e:
            FrameworkLogger.warning(f"Could not open log file: {e}")
            self.file_handle = None

        intent_line = f"Intent: {intent}" if intent else ""
        header = f"""
================================================================================
                    INTENT-BASED API EXECUTION LOG
================================================================================
Session Start: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}
{intent_line}
================================================================================
"""
        self.log(header)

    def end_session(self):
        """End the logging session."""
        if self.session_start:
            duration = datetime.now() - self.session_start
            footer = f"""
================================================================================
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


# Convenience aliases
log = FrameworkLogger
logger = FrameworkLogger

# Pre-instantiated intent logger (can be used directly)
intent_logger = IntentLogger()
