"""
BBAP-Sec AI Attack Lab — Logger Singleton
==========================================
Centralized logging for every module in the pipeline.

Usage:
    from src.utils.logger import LoggerSingleton, get_project_root
    LoggerSingleton.setup(get_project_root())
    logger = LoggerSingleton.get_logger("adversarial")
    logger.info("Starting FGSM attack with epsilon=0.03")

Log files are written to: <project_root>/logs/<module_name>.log
A combined log is also written to: <project_root>/logs/pipeline.log
All logs append — one persistent file per module across all runs.
"""

import os
import sys
import logging
import threading
from pathlib import Path
from datetime import datetime


# ──────────────────────────────────────────────
# Project Path Helpers
# ──────────────────────────────────────────────

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_project_root():
    """Return the project root directory."""
    return os.environ.get("BBAP_PROJECT_ROOT", PROJECT_ROOT)


def get_working_dir():
    """Return the working directory (defaults to project root)."""
    return os.environ.get("BBAP_WORKING_DIR", get_project_root())


def get_dataset_dir():
    """Return the dataset directory."""
    return os.environ.get("BBAP_DATASET_DIR", os.path.join(get_project_root(), "datasets", "data"))


def get_log_dir():
    """Return the log directory, creating it if needed."""
    log_dir = os.path.join(get_working_dir(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_results_dir():
    """Return the results directory, creating it if needed."""
    results_dir = os.path.join(get_working_dir(), "results")
    os.makedirs(results_dir, exist_ok=True)
    return results_dir


# ──────────────────────────────────────────────
# ANSI Color Codes for Console Output
# ──────────────────────────────────────────────

class _Colors:
    RESET    = "\033[0m"
    BOLD     = "\033[1m"
    DIM      = "\033[2m"
    # BBAP-Sec brand palette
    EMERALD  = "\033[38;5;35m"   # green
    GOLD     = "\033[38;5;178m"  # gold/amber
    COPPER   = "\033[38;5;173m"  # copper/bronze
    RED      = "\033[38;5;196m"  # errors
    CYAN     = "\033[38;5;44m"   # debug
    GRAY     = "\033[38;5;245m"  # timestamps

    LEVEL_COLORS = {
        "DEBUG":    CYAN,
        "INFO":     EMERALD,
        "WARNING":  GOLD,
        "ERROR":    RED,
        "CRITICAL": BOLD + RED,
    }


class _ColoredConsoleFormatter(logging.Formatter):
    """Console formatter with ANSI colors and aligned columns."""

    def format(self, record):
        c = _Colors
        level_color = c.LEVEL_COLORS.get(record.levelname, c.RESET)
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]

        # Pad level name for alignment
        level_str = f"{level_color}{record.levelname:<8}{c.RESET}"
        module_str = f"{c.COPPER}{c.BOLD}[{record.name}]{c.RESET}"
        time_str = f"{c.GRAY}{timestamp}{c.RESET}"

        msg = record.getMessage()

        # Step detection: highlight lines starting with [1/3], [STEP], etc.
        if msg.startswith("[") and "]" in msg[:8]:
            bracket_end = msg.index("]") + 1
            step_tag = msg[:bracket_end]
            rest = msg[bracket_end:]
            msg = f"{c.GOLD}{c.BOLD}{step_tag}{c.RESET}{rest}"
        # Separator lines
        elif msg.startswith("=" * 10) or msg.startswith("─" * 10):
            msg = f"{c.EMERALD}{msg}{c.RESET}"
        # Result/metric lines
        elif ":" in msg and any(kw in msg.lower() for kw in ["accuracy", "rate", "fidelity", "loss", "drop", "evasion"]):
            parts = msg.split(":", 1)
            msg = f"{c.DIM}{parts[0]}:{c.RESET}{c.BOLD}{parts[1]}{c.RESET}"

        return f"  {time_str}  {level_str} {module_str}  {msg}"


class _FileFormatter(logging.Formatter):
    """Clean file formatter without ANSI codes."""

    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"{timestamp}  {record.levelname:<8}  [{record.name}]  {record.getMessage()}"


# ──────────────────────────────────────────────
# LoggerSingleton
# ──────────────────────────────────────────────

class LoggerSingleton:
    """
    Thread-safe singleton logger factory.

    Call setup() once at the start of any script, then get_logger("module_name")
    to get a named child logger. All loggers write to:
        - Console (colored, human-friendly)
        - logs/pipeline.log (combined, all modules, appended)
        - logs/<module_name>.log (per-module, appended)

    Each run appends to the same log file — no timestamp suffixes.
    A session separator is printed at the start of each run.

    Example:
        LoggerSingleton.setup(get_project_root())
        logger = LoggerSingleton.get_logger("adversarial")
        logger.info("[1/3] Loading dataset...")
    """

    _lock = threading.RLock()
    _initialized = False
    _log_dir = None
    _session_id = None
    _pipeline_handler = None
    _console_handler = None
    _module_loggers = {}

    @classmethod
    def setup(cls, working_dir=None, level=logging.DEBUG, console_level=logging.INFO):
        """
        Initialize the logging system. Safe to call multiple times (idempotent).

        Args:
            working_dir: Project root or working directory
            level: File log level (default: DEBUG — captures everything)
            console_level: Console log level (default: INFO)
        """
        with cls._lock:
            if cls._initialized:
                return

            working_dir = working_dir or get_working_dir()
            cls._log_dir = os.path.join(working_dir, "logs")
            os.makedirs(cls._log_dir, exist_ok=True)

            cls._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Root logger for the project namespace
            root = logging.getLogger("bbap")
            root.setLevel(level)
            root.propagate = False

            # Remove any existing handlers (idempotency)
            root.handlers.clear()

            # Console handler — colored, INFO level (stderr = standard for logs)
            cls._console_handler = logging.StreamHandler(sys.stderr)
            cls._console_handler.setLevel(console_level)
            cls._console_handler.setFormatter(_ColoredConsoleFormatter())
            root.addHandler(cls._console_handler)

            # Pipeline-wide file handler — captures DEBUG+ from all modules (append mode)
            pipeline_log = os.path.join(cls._log_dir, "pipeline.log")
            cls._pipeline_handler = logging.FileHandler(pipeline_log, mode="a", encoding="utf-8")
            cls._pipeline_handler.setLevel(level)
            cls._pipeline_handler.setFormatter(_FileFormatter())
            root.addHandler(cls._pipeline_handler)

            cls._initialized = True

            # Log startup
            startup_logger = cls.get_logger("system")
            startup_logger.info("=" * 60)
            startup_logger.info("BBAP-Sec AI Attack Lab — Logging initialized")
            startup_logger.info(f"Session ID: {cls._session_id}")
            startup_logger.info(f"Log directory: {cls._log_dir}")
            startup_logger.info(f"Pipeline log: {pipeline_log}")
            startup_logger.info("=" * 60)

    @classmethod
    def get_logger(cls, module_name: str) -> logging.Logger:
        """
        Get a named logger for a specific module.

        Creates (or reuses) a per-module log file:
            logs/<module_name>.log

        Args:
            module_name: Short name like "adversarial", "data_poisoning", "target_model"

        Returns:
            logging.Logger instance
        """
        if not cls._initialized:
            cls.setup()

        with cls._lock:
            if module_name in cls._module_loggers:
                return cls._module_loggers[module_name]

            # Create child logger under the bbap namespace
            logger = logging.getLogger(f"bbap.{module_name}")
            logger.setLevel(logging.DEBUG)
            logger.propagate = True  # Also sends to pipeline log via root

            # Per-module file handler (fixed name, append mode)
            module_log = os.path.join(cls._log_dir, f"{module_name}.log")
            module_handler = logging.FileHandler(module_log, mode="a", encoding="utf-8")
            module_handler.setLevel(logging.DEBUG)
            module_handler.setFormatter(_FileFormatter())
            logger.addHandler(module_handler)

            cls._module_loggers[module_name] = logger

            logger.debug(f"Logger initialized → {module_log}")
            return logger

    @classmethod
    def get_log_dir(cls):
        """Return the current session's log directory."""
        return cls._log_dir

    @classmethod
    def get_session_id(cls):
        """Return the current session ID (timestamp string)."""
        return cls._session_id

    @classmethod
    def shutdown(cls):
        """Flush and close all handlers."""
        with cls._lock:
            root = logging.getLogger("bbap")
            for handler in root.handlers[:]:
                handler.flush()
                handler.close()
                root.removeHandler(handler)
            for name, logger in cls._module_loggers.items():
                for handler in logger.handlers[:]:
                    handler.flush()
                    handler.close()
                    logger.removeHandler(handler)
            cls._module_loggers.clear()
            cls._initialized = False


# ──────────────────────────────────────────────
# Convenience: auto-setup + quick logger
# ──────────────────────────────────────────────

def setup_logger(working_dir=None):
    """Shortcut to initialize the logging system."""
    LoggerSingleton.setup(working_dir)


def get_logger(module_name: str) -> logging.Logger:
    """Shortcut to get a named logger (auto-initializes if needed)."""
    return LoggerSingleton.get_logger(module_name)
