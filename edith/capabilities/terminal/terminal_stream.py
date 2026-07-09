"""
Terminal Capability — Output Streaming

TerminalStream reads stdout and stderr from a running process on
dedicated daemon threads, classifies each line by StreamLevel, and
publishes events to the Event Bus without blocking the Orchestrator.
"""

from __future__ import annotations

import re
import threading
from datetime import datetime
from typing import IO

from edith.capabilities.terminal.terminal_models import OutputLine, SessionStatus, StreamLevel
from edith.capabilities.terminal.terminal_session import TerminalSession
from edith.core.events import AppEvent, event_bus
from edith.utils.logger import logger


# ---------------------------------------------------------------------------
# Keyword patterns for line classification
# ---------------------------------------------------------------------------

_ERROR_PATTERNS = re.compile(
    r"\b(error|exception|fatal|fail(ed|ure)?|crash(ed)?|traceback|panic)\b",
    re.IGNORECASE,
)
_WARNING_PATTERNS = re.compile(
    r"\b(warn(ing)?|deprecated?|deprecation|caution|notice)\b",
    re.IGNORECASE,
)
_SUCCESS_PATTERNS = re.compile(
    r"\b(success(ful(ly)?)?|done|complete(d)?|pass(ed)?|built|compiled|ready)\b"
    r"|✓|✔|🎉|✅",
    re.IGNORECASE,
)


class TerminalStream:
    """
    Manages two background daemon threads (stdout + stderr) that read
    process output line by line, classify each line, and publish events.
    """

    def __init__(self, session: TerminalSession, encoding: str = "utf-8"):
        self._session = session
        self._encoding = encoding
        self._stdout_thread: threading.Thread | None = None
        self._stderr_thread: threading.Thread | None = None

    def start(self) -> None:
        """Start background reader threads. Call after process.Popen() succeeds."""
        process = self._session._process
        if process is None:
            raise RuntimeError("Cannot start stream: process handle is None")

        if process.stdout:
            self._stdout_thread = threading.Thread(
                target=self._read_loop,
                args=(process.stdout, "stdout"),
                name=f"stream-stdout-{self._session.session_id[:8]}",
                daemon=True,
            )
            self._stdout_thread.start()

        if process.stderr:
            self._stderr_thread = threading.Thread(
                target=self._read_loop,
                args=(process.stderr, "stderr"),
                name=f"stream-stderr-{self._session.session_id[:8]}",
                daemon=True,
            )
            self._stderr_thread.start()

        # A separate thread monitors process exit and publishes COMMAND_FINISHED
        monitor = threading.Thread(
            target=self._monitor_exit,
            name=f"stream-monitor-{self._session.session_id[:8]}",
            daemon=True,
        )
        monitor.start()

    def _read_loop(self, pipe: IO[bytes], source: str) -> None:
        try:
            for raw_line in iter(pipe.readline, b""):
                if not raw_line:
                    break
                text = raw_line.decode(self._encoding, errors="replace").rstrip("\r\n")
                level = self._classify(text, source)
                line = OutputLine(line=text, level=level, source=source)
                self._session.append_output(line)
                event_bus.publish(
                    AppEvent.COMMAND_OUTPUT,
                    {
                        "session_id": self._session.session_id,
                        "line": text,
                        "level": level.value,
                        "source": source,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
        except (OSError, ValueError):
            # Pipe closed or process died
            pass
        except Exception as e:
            logger.error(
                f"Stream read error ({source}) "
                f"session={self._session.session_id[:8]}: {e}"
            )

    def _monitor_exit(self) -> None:
        """Wait for the process to exit, update session state, publish final event."""
        process = self._session._process
        if process is None:
            return

        exit_code = process.wait()

        # Wait for reader threads to drain before marking completed
        if self._stdout_thread:
            self._stdout_thread.join(timeout=2)
        if self._stderr_thread:
            self._stderr_thread.join(timeout=2)

        self._session.mark_completed(exit_code)

        event_type = (
            AppEvent.COMMAND_FINISHED
            if exit_code == 0
            else AppEvent.COMMAND_FAILED
        )
        event_bus.publish(
            event_type,
            {
                "session_id": self._session.session_id,
                "command": self._session.command,
                "cwd": self._session.cwd,
                "exit_code": exit_code,
                "duration_seconds": self._session.duration_seconds,
                "group_id": self._session.group_id,
            },
        )
        logger.info(
            f"Session {self._session.session_id[:8]} exited with code {exit_code} "
            f"({self._session.duration_seconds:.1f}s)"
        )

    @staticmethod
    def _classify(line: str, source: str) -> StreamLevel:
        """Classify a line of output into a StreamLevel."""
        if source == "stderr":
            # stderr is always classified as STDERR first,
            # but we further refine it if it matches error keywords
            if _ERROR_PATTERNS.search(line):
                return StreamLevel.ERROR
            return StreamLevel.STDERR

        # stdout classification by keyword
        if _ERROR_PATTERNS.search(line):
            return StreamLevel.ERROR
        if _WARNING_PATTERNS.search(line):
            return StreamLevel.WARNING
        if _SUCCESS_PATTERNS.search(line):
            return StreamLevel.SUCCESS
        return StreamLevel.STDOUT
