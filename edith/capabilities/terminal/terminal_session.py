"""
Terminal Capability — Session Model + State Machine

Each TerminalSession represents the complete lifecycle of one process
spawned by EDITH. Sessions are managed by TerminalProcessManager.
"""

from __future__ import annotations

import subprocess
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from edith.capabilities.terminal.terminal_models import (
    OutputLine,
    SessionStatus,
    StreamLevel,
)
from edith.utils.logger import logger


class TerminalSession:
    """
    Represents one running or completed process managed by EDITH.

    NOT a Pydantic model because it holds live OS handles (Popen, Lock)
    which are not serializable. Use .to_dict() for serialization.
    """

    MAX_OUTPUT_LINES = 5000  # Rolling buffer limit

    def __init__(
        self,
        command: str,
        shell_id: str,
        cwd: str,
        group_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        label: Optional[str] = None,
    ):
        self.session_id: str = str(uuid.uuid4())
        self.command: str = command
        self.shell_id: str = shell_id
        self.cwd: str = cwd
        self.group_id: Optional[str] = group_id
        self.workspace_id: Optional[str] = workspace_id
        self.env: Optional[Dict[str, str]] = env
        self.label: Optional[str] = label or command[:40]

        self.pid: Optional[int] = None
        self.status: SessionStatus = SessionStatus.PENDING
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None
        self.exit_code: Optional[int] = None

        # Output buffer
        self.output_lines: List[OutputLine] = []
        self._output_lock = threading.Lock()

        # OS process handle — excluded from serialisation
        self._process: Optional[subprocess.Popen] = None
        self._stdin_lock = threading.Lock()

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def mark_running(self, process: subprocess.Popen) -> None:
        self._process = process
        self.pid = process.pid
        self.status = SessionStatus.RUNNING
        logger.debug(f"Session {self.session_id[:8]} RUNNING (PID={self.pid})")

    def mark_completed(self, exit_code: int) -> None:
        self.exit_code = exit_code
        self.end_time = datetime.now()
        if self.status == SessionStatus.CANCELLED:
            # Preserve cancelled status instead of overwriting with FAILED
            logger.debug(f"Session {self.session_id[:8]} completed with exit={exit_code} (was CANCELLED)")
            return
        self.status = SessionStatus.COMPLETED if exit_code == 0 else SessionStatus.FAILED
        logger.debug(
            f"Session {self.session_id[:8]} "
            f"{'COMPLETED' if exit_code == 0 else 'FAILED'} (exit={exit_code})"
        )

    def mark_cancelled(self) -> None:
        self.end_time = datetime.now()
        self.status = SessionStatus.CANCELLED
        logger.debug(f"Session {self.session_id[:8]} CANCELLED")

    # ------------------------------------------------------------------
    # Output management
    # ------------------------------------------------------------------

    def append_output(self, line: OutputLine) -> None:
        with self._output_lock:
            if len(self.output_lines) >= self.MAX_OUTPUT_LINES:
                # Rolling buffer: discard oldest
                self.output_lines.pop(0)
            self.output_lines.append(line)

    def get_last_output(self, n: int = 20) -> List[OutputLine]:
        with self._output_lock:
            return self.output_lines[-n:]

    # ------------------------------------------------------------------
    # Interactive stdin
    # ------------------------------------------------------------------

    def send_input(self, text: str) -> bool:
        """Write text + newline to process stdin. Returns True on success."""
        with self._stdin_lock:
            if self._process is None or self._process.stdin is None:
                return False
            if self.status != SessionStatus.RUNNING:
                return False
            try:
                self._process.stdin.write((text + "\n").encode("utf-8"))
                self._process.stdin.flush()
                return True
            except (OSError, BrokenPipeError) as e:
                logger.warning(f"Session {self.session_id[:8]}: stdin write failed: {e}")
                return False

    def send_ctrl_c(self) -> bool:
        """Send SIGINT / CTRL_C_EVENT to the process."""
        if self._process is None or self.status != SessionStatus.RUNNING:
            return False
        try:
            import sys
            if sys.platform == "win32":
                import signal
                self._process.send_signal(signal.CTRL_C_EVENT)
            else:
                import signal
                self._process.send_signal(signal.SIGINT)
            return True
        except (OSError, ProcessLookupError) as e:
            logger.warning(f"Session {self.session_id[:8]}: CTRL+C failed: {e}")
            return False

    def send_ctrl_break(self) -> bool:
        """Send CTRL_BREAK_EVENT (Windows only)."""
        if self._process is None or self.status != SessionStatus.RUNNING:
            return False
        try:
            import signal, sys
            if sys.platform == "win32":
                self._process.send_signal(signal.CTRL_BREAK_EVENT)
                return True
        except (OSError, ProcessLookupError) as e:
            logger.warning(f"Session {self.session_id[:8]}: CTRL+BREAK failed: {e}")
        return False

    # ------------------------------------------------------------------
    # Duration helper
    # ------------------------------------------------------------------

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "command": self.command,
            "shell_id": self.shell_id,
            "cwd": self.cwd,
            "label": self.label,
            "pid": self.pid,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "group_id": self.group_id,
            "workspace_id": self.workspace_id,
            "output_line_count": len(self.output_lines),
        }

    def __repr__(self) -> str:
        return (
            f"<TerminalSession id={self.session_id[:8]} "
            f"status={self.status.value} cmd='{self.command[:30]}'>"
        )
