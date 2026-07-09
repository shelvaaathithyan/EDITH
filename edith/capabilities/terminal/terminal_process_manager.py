"""
Terminal Capability — Process Manager

Single source of truth for all processes and process groups
spawned by EDITH. Thread-safe via RLock.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from typing import Dict, List, Optional

from edith.capabilities.terminal.terminal_exceptions import (
    ProcessGroupError,
    SessionNotFoundError,
)
from edith.capabilities.terminal.terminal_models import GroupStatus, ProcessGroup, SessionStatus
from edith.capabilities.terminal.terminal_session import TerminalSession
from edith.capabilities.terminal.terminal_shell_profiles import ShellProfile, shell_registry
from edith.capabilities.terminal.terminal_stream import TerminalStream
from edith.core.events import AppEvent, event_bus
from edith.utils.logger import logger


class TerminalProcessManager:
    """
    Manages all terminal sessions and process groups.
    All public methods are thread-safe.
    """

    def __init__(self):
        self._sessions: Dict[str, TerminalSession] = {}
        self._groups: Dict[str, ProcessGroup] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start(
        self,
        command: str,
        cwd: str,
        shell_profile: ShellProfile,
        env: Optional[Dict[str, str]] = None,
        group_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        label: Optional[str] = None,
    ) -> TerminalSession:
        """
        Spawn a new process for the given command.
        Returns immediately with the session object (non-blocking).
        The process runs in a background daemon thread.
        """
        session = TerminalSession(
            command=command,
            shell_id=shell_profile.id,
            cwd=cwd,
            group_id=group_id,
            workspace_id=workspace_id,
            env=env,
            label=label,
        )

        with self._lock:
            self._sessions[session.session_id] = session
            if group_id and group_id in self._groups:
                self._groups[group_id].session_ids.append(session.session_id)
                self._groups[group_id].status = GroupStatus.RUNNING

        # Build the full command list for the shell
        full_cmd = self._build_command(command, shell_profile)

        # Build env
        process_env = self._build_env(shell_profile, env)

        try:
            creation_flags = 0
            if sys.platform == "win32":
                # CREATE_NEW_PROCESS_GROUP allows sending CTRL_BREAK_EVENT
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

            process = subprocess.Popen(
                full_cmd,
                cwd=cwd,
                env=process_env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags,
            )

            session.mark_running(process)

            # Start streaming (non-blocking daemon threads)
            stream = TerminalStream(session, encoding=shell_profile.encoding)
            stream.start()

            event_bus.publish(
                AppEvent.COMMAND_STARTED,
                {
                    "session_id": session.session_id,
                    "command": command,
                    "cwd": cwd,
                    "shell": shell_profile.id,
                    "pid": session.pid,
                    "group_id": group_id,
                },
            )
            logger.info(
                f"Process started: PID={session.pid} "
                f"cmd='{command[:50]}' cwd='{cwd}'"
            )

        except FileNotFoundError:
            session.mark_completed(-1)
            logger.error(f"Executable not found for: {command}")
            raise

        except Exception as e:
            session.mark_completed(-1)
            logger.error(f"Failed to start process: {e}")
            raise

        return session

    def stop(self, session_id: str, force: bool = False) -> bool:
        """
        Gracefully terminate a session (SIGTERM / CTRL_BREAK_EVENT).
        Falls back to SIGKILL / TerminateProcess if force=True.
        Returns True on success.
        """
        session = self._get_session_or_raise(session_id)

        if session.status != SessionStatus.RUNNING:
            logger.info(f"Session {session_id[:8]} is not running; nothing to stop.")
            return True

        process = session._process
        if process is None:
            return False

        try:
            if force:
                process.kill()
                logger.info(f"Session {session_id[:8]}: force-killed (SIGKILL).")
            else:
                if sys.platform == "win32":
                    # Graceful: CTRL_BREAK to process group
                    import signal
                    try:
                        process.send_signal(signal.CTRL_BREAK_EVENT)
                    except Exception:
                        process.terminate()
                else:
                    process.terminate()
                logger.info(f"Session {session_id[:8]}: graceful stop sent.")

            session.mark_cancelled()
            event_bus.publish(
                AppEvent.PROCESS_KILLED if force else AppEvent.COMMAND_CANCELLED,
                {"session_id": session_id, "force": force},
            )
            return True

        except (OSError, ProcessLookupError) as e:
            logger.warning(f"Stop failed for session {session_id[:8]}: {e}")
            return False

    def restart(self, session_id: str) -> TerminalSession:
        """
        Stop the existing session and start a new one with the same command/cwd.
        Returns the new TerminalSession.
        """
        session = self._get_session_or_raise(session_id)
        self.stop(session_id, force=False)

        profile = shell_registry.resolve(session.shell_id)
        return self.start(
            command=session.command,
            cwd=session.cwd,
            shell_profile=profile,
            env=session.env,
            group_id=session.group_id,
            workspace_id=session.workspace_id,
            label=session.label,
        )

    # ------------------------------------------------------------------
    # Interactive I/O
    # ------------------------------------------------------------------

    def send_input(self, session_id: str, text: str) -> bool:
        session = self._get_session_or_raise(session_id)
        return session.send_input(text)

    def send_ctrl_c(self, session_id: str) -> bool:
        session = self._get_session_or_raise(session_id)
        return session.send_ctrl_c()

    def send_ctrl_break(self, session_id: str) -> bool:
        session = self._get_session_or_raise(session_id)
        return session.send_ctrl_break()

    # ------------------------------------------------------------------
    # Process Groups
    # ------------------------------------------------------------------

    def create_group(self, name: str) -> ProcessGroup:
        group = ProcessGroup(name=name)
        with self._lock:
            self._groups[group.group_id] = group
        logger.info(f"Process group created: '{name}' ({group.group_id[:8]})")
        event_bus.publish(
            AppEvent.PROCESS_GROUP_CREATED,
            {"group_id": group.group_id, "name": name},
        )
        return group

    def stop_group(self, group_id: str, force: bool = False) -> List[bool]:
        """Stop all sessions in a process group in parallel."""
        with self._lock:
            group = self._groups.get(group_id)
        if not group:
            raise ProcessGroupError(group_id, "not found")

        results: List[bool] = []
        threads: List[threading.Thread] = []
        lock = threading.Lock()

        def _stop(sid: str) -> None:
            result = self.stop(sid, force=force)
            with lock:
                results.append(result)

        for sid in list(group.session_ids):
            t = threading.Thread(target=_stop, args=(sid,), daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10)

        with self._lock:
            group.status = GroupStatus.STOPPED

        event_bus.publish(
            AppEvent.PROCESS_GROUP_STOPPED,
            {"group_id": group_id, "name": group.name},
        )
        return results

    def get_group(self, group_id: str) -> Optional[ProcessGroup]:
        with self._lock:
            return self._groups.get(group_id)

    def list_groups(self) -> List[ProcessGroup]:
        with self._lock:
            return list(self._groups.values())

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def list_running(self) -> List[TerminalSession]:
        with self._lock:
            return [
                s for s in self._sessions.values()
                if s.status == SessionStatus.RUNNING
            ]

    def list_all(self) -> List[TerminalSession]:
        with self._lock:
            return list(self._sessions.values())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_session_or_raise(self, session_id: str) -> TerminalSession:
        session = self.get_session(session_id)
        if not session:
            raise SessionNotFoundError(session_id)
        return session

    @staticmethod
    def _build_command(command: str, profile: ShellProfile) -> List[str]:
        """Wrap the user command in the shell's invocation syntax."""
        exe = profile.executable
        shell_args = profile.args.copy()

        if exe in ("pwsh", "powershell"):
            # PowerShell: -Command flag to execute a string
            return [exe] + shell_args + ["-Command", command]
        elif exe == "cmd":
            # CMD: /C to execute then exit
            return [exe] + shell_args + ["/C", command]
        elif exe in ("bash", "zsh", "sh"):
            return [exe] + shell_args + ["-c", command]
        elif exe == "wsl":
            return [exe] + shell_args + ["--", "bash", "-c", command]
        else:
            # Generic fallback: pass as -c argument
            return [exe] + shell_args + ["-c", command]

    @staticmethod
    def _build_env(
        profile: ShellProfile,
        overrides: Optional[Dict[str, str]],
    ) -> Dict[str, str]:
        env = os.environ.copy()
        # Apply shell profile env vars
        env.update(profile.env_vars)
        # Apply workspace / session overrides
        if overrides:
            env.update(overrides)
        return env


# Global singleton
process_manager = TerminalProcessManager()
