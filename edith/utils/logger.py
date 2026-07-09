"""
EDITH Structured Logging System.
Provides per-subsystem log channels with automatic file rotation.
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler

# Configuration
LOG_DIR = Path("edith/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

# Channel → filename mapping
_CHANNEL_MAP = {
    "edith.core": "orchestrator.log",
    "edith.ai": "planner.log",
    "edith.voice": "voice.log",
    "edith.wake": "voice.log",
    "edith.capabilities": "capabilities.log",
    "edith.capabilities.vision": "vision.log",
    "edith.capabilities.spotify": "spotify.log",
    "edith.capabilities.terminal": "terminal.log",
    "edith.capabilities.filesystem": "filesystem.log",
    "edith.capabilities.desktop": "desktop.log",
    "edith.capabilities.browser": "browser.log",
    "edith.memory": "memory.log",
    "edith.permission": "orchestrator.log",
    "edith.interaction": "orchestrator.log",
    "edith.ui": "orchestrator.log",
    "edith.sdk": "capabilities.log",
}

_FILE_FORMAT = logging.Formatter(
    fmt="%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Cache of created file handlers to avoid duplicates
_handler_cache: dict[str, RotatingFileHandler] = {}


def _get_file_handler(filename: str) -> RotatingFileHandler:
    """Returns a cached or new RotatingFileHandler for the given filename."""
    if filename not in _handler_cache:
        filepath = LOG_DIR / filename
        handler = RotatingFileHandler(
            filepath, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(_FILE_FORMAT)
        _handler_cache[filename] = handler
    return _handler_cache[filename]


def _resolve_channel(name: str) -> str:
    """Resolves a logger name to a log filename using longest-prefix match."""
    best_match = "orchestrator.log"
    best_len = 0
    for prefix, filename in _CHANNEL_MAP.items():
        if name.startswith(prefix) and len(prefix) > best_len:
            best_match = filename
            best_len = len(prefix)
    return best_match


# Global error log — captures ALL errors across every subsystem
_error_handler = _get_file_handler("errors.log")
_error_handler.setLevel(logging.ERROR)

# Console handler (Rich)
_console_handler = RichHandler(rich_tracebacks=True, markup=True)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter("%(message)s"))


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger with the given name, routed to the appropriate log file.
    Each logger writes to:
      1. Its subsystem-specific log file (DEBUG+)
      2. The global errors.log (ERROR+)
      3. The Rich console (INFO+)
    """
    log = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if not log.handlers:
        log.setLevel(logging.DEBUG)
        log.propagate = False

        # Subsystem-specific file
        channel_file = _resolve_channel(name)
        log.addHandler(_get_file_handler(channel_file))

        # Global error aggregator
        log.addHandler(_error_handler)

        # Console
        log.addHandler(_console_handler)

    return log


# Default logger for convenience imports
logger = get_logger("edith")
