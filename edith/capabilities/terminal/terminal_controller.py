"""
Terminal Capability — High-level Controller

Orchestrates command execution by combining shell profile selection,
cwd resolution, workspace env injection, and validation into a single
clean API used by TerminalCapability action handlers.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from edith.capabilities.terminal.terminal_exceptions import ShellNotFoundError, WorkingDirectoryError
from edith.capabilities.terminal.terminal_models import SessionStatus
from edith.capabilities.terminal.terminal_process_manager import TerminalProcessManager, process_manager
from edith.capabilities.terminal.terminal_session import TerminalSession
from edith.capabilities.terminal.terminal_shell_profiles import ShellProfile, shell_registry
from edith.capabilities.terminal.terminal_utils import resolve_cwd
from edith.capabilities.terminal.terminal_validator import TerminalValidator
from edith.capabilities.terminal.terminal_workspace import WorkspaceInfo, workspace_manager
from edith.core.events import AppEvent, event_bus
from edith.utils.logger import logger


class TerminalController:
    """
    High-level terminal command orchestration.
    Used exclusively by TerminalCapability action handlers.
    """

    def __init__(
        self,
        pm: TerminalProcessManager = process_manager,
    ):
        self._pm = pm

    def run_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        shell_id: Optional[str] = None,
        env_overrides: Optional[Dict[str, str]] = None,
        group_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        label: Optional[str] = None,
        context_cwd: Optional[str] = None,
    ) -> TerminalSession:
        """
        Full pipeline:
        1. Validate command (block-list + executable check)
        2. Resolve working directory
        3. Resolve shell profile
        4. Merge env vars (workspace + venv + overrides)
        5. Start process (non-blocking)
        """
        # Validate
        TerminalValidator.validate_command(command)

        # Resolve cwd
        workspace = workspace_manager.get_active_workspace()
        ws_root = workspace.root_path if workspace else None
        resolved_cwd = resolve_cwd(cwd, context_cwd, ws_root)
        TerminalValidator.validate_working_directory(resolved_cwd)

        # Resolve shell profile
        profile = shell_registry.resolve(shell_id)

        # Build env
        env: Dict[str, str] = {}
        if workspace:
            env.update(workspace_manager.get_env_for_workspace(workspace))
        if env_overrides:
            env.update(env_overrides)

        return self._pm.start(
            command=command,
            cwd=resolved_cwd,
            shell_profile=profile,
            env=env if env else None,
            group_id=group_id,
            workspace_id=workspace_id or (workspace.workspace_id if workspace else None),
            label=label,
        )

    def open_terminal_window(self, shell_id: Optional[str] = None, cwd: Optional[str] = None) -> bool:
        """
        Open a visible terminal window using the shell profile's window mode.
        Returns True on success.
        """
        profile = shell_registry.resolve(shell_id)
        resolved_cwd = cwd or (
            workspace_manager.get_active_workspace().root_path
            if workspace_manager.get_active_workspace()
            else str(Path.home())
        )

        try:
            cmd = [profile.executable] + profile.args
            if sys.platform == "win32":
                subprocess.Popen(
                    cmd,
                    cwd=resolved_cwd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:
                subprocess.Popen(cmd, cwd=resolved_cwd)

            event_bus.publish(
                AppEvent.TERMINAL_OPENED,
                {"shell": profile.id, "cwd": resolved_cwd},
            )
            return True
        except Exception as e:
            logger.error(f"Failed to open terminal window: {e}")
            return False

    def stop_session(self, session_id: str, force: bool = False) -> bool:
        return self._pm.stop(session_id, force=force)

    def restart_session(self, session_id: str) -> TerminalSession:
        return self._pm.restart(session_id)

    def send_input(self, session_id: str, text: str) -> bool:
        return self._pm.send_input(session_id, text)

    def send_ctrl_c(self, session_id: str) -> bool:
        return self._pm.send_ctrl_c(session_id)


# Global singleton
terminal_controller = TerminalController()
