"""
Terminal Capability — Workspace Manager

Maintains project-aware execution contexts. A Workspace combines:
- A root directory
- Detected project types and package manager
- Git root, virtualenv path, docker-compose path
- Cached environment tool versions
- Runtime environment variable overrides
"""

from __future__ import annotations

import threading
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from edith.capabilities.terminal.terminal_env_detector import EnvironmentDetector
from edith.capabilities.terminal.terminal_exceptions import WorkspaceError
from edith.capabilities.terminal.terminal_models import (
    EnvironmentInfo,
    PackageManager,
    ProjectType,
    WorkspaceInfo,
)
from edith.capabilities.terminal.terminal_project_detector import ProjectDetector
from edith.core.events import AppEvent, event_bus
from edith.utils.logger import logger


class WorkspaceManager:
    """
    Manages named developer workspaces. Each workspace captures the full
    project context needed to intelligently dispatch commands.
    """

    def __init__(self):
        self._workspaces: Dict[str, WorkspaceInfo] = {}
        self._active_workspace_id: Optional[str] = None
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Open / switch
    # ------------------------------------------------------------------

    def open_workspace(self, path: str, run_env_detection: bool = True) -> WorkspaceInfo:
        """
        Open a directory as a workspace. Detects project type, git root,
        venv, docker-compose, and (optionally) tool versions.
        """
        root = Path(path).resolve()
        if not root.is_dir():
            raise WorkspaceError(str(root), "path is not a directory or does not exist")

        name = root.name
        logger.info(f"Opening workspace: {root}")

        # Project detection
        project_types, package_manager = ProjectDetector.detect(root)
        git_root = ProjectDetector.find_git_root(root)
        venv_path = ProjectDetector.find_venv(root)
        docker_compose = ProjectDetector.find_docker_compose(root)

        # Tool environment detection (may take a few seconds)
        env_info = EnvironmentInfo()
        if run_env_detection:
            try:
                env_info = EnvironmentDetector.detect(cwd=str(root))
            except Exception as e:
                logger.warning(f"Environment detection failed: {e}")

        workspace = WorkspaceInfo(
            name=name,
            root_path=str(root),
            project_types=project_types,
            package_manager=package_manager,
            git_root=git_root,
            venv_path=venv_path,
            docker_compose_path=docker_compose,
            environment=env_info,
        )

        with self._lock:
            self._workspaces[workspace.workspace_id] = workspace
            self._active_workspace_id = workspace.workspace_id

        logger.info(
            f"Workspace '{name}': types={[t.value for t in project_types]}, "
            f"pm={package_manager.value if package_manager else None}, "
            f"git={'yes' if git_root else 'no'}, "
            f"venv={'yes' if venv_path else 'no'}"
        )

        event_bus.publish(AppEvent.WORKSPACE_OPENED, workspace.model_dump())
        event_bus.publish(
            AppEvent.PROJECT_DETECTED,
            {
                "workspace_id": workspace.workspace_id,
                "types": [t.value for t in project_types],
                "package_manager": package_manager.value if package_manager else None,
            },
        )
        if run_env_detection:
            event_bus.publish(
                AppEvent.ENV_DETECTED,
                {
                    "workspace_id": workspace.workspace_id,
                    "available_tools": env_info.available_tools,
                },
            )

        return workspace

    def get_active_workspace(self) -> Optional[WorkspaceInfo]:
        with self._lock:
            if self._active_workspace_id:
                return self._workspaces.get(self._active_workspace_id)
        return None

    def set_active_workspace(self, workspace_id: str) -> None:
        with self._lock:
            if workspace_id not in self._workspaces:
                raise WorkspaceError(workspace_id, "workspace not found")
            self._active_workspace_id = workspace_id

    def switch_workspace(self, workspace_id: str) -> WorkspaceInfo:
        self.set_active_workspace(workspace_id)
        workspace = self._workspaces[workspace_id]
        event_bus.publish(AppEvent.WORKSPACE_SWITCHED, workspace.model_dump())
        return workspace

    def get_workspace(self, workspace_id: str) -> Optional[WorkspaceInfo]:
        with self._lock:
            return self._workspaces.get(workspace_id)

    def list_workspaces(self) -> List[WorkspaceInfo]:
        with self._lock:
            return list(self._workspaces.values())

    # ------------------------------------------------------------------
    # venv activation
    # ------------------------------------------------------------------

    def build_venv_env(self, workspace: WorkspaceInfo) -> Dict[str, str]:
        """
        Returns a dict of env var overrides that activate the workspace's
        Python virtualenv. These are injected into the process env at launch.
        Works for all shells — no shell-specific activation scripts needed.
        """
        import os
        if not workspace.venv_path:
            return {}

        venv = Path(workspace.venv_path)
        scripts_dir = venv / ("Scripts" if __import__("sys").platform == "win32" else "bin")

        current_path = os.environ.get("PATH", "")
        return {
            "VIRTUAL_ENV": str(venv),
            "PATH": str(scripts_dir) + os.pathsep + current_path,
            "PYTHONHOME": "",    # clear to prevent conflicts
        }

    # ------------------------------------------------------------------
    # Environment overrides
    # ------------------------------------------------------------------

    def set_env_override(
        self, workspace_id: str, key: str, value: str
    ) -> None:
        with self._lock:
            ws = self._workspaces.get(workspace_id)
            if ws:
                ws.env_overrides[key] = value

    def get_env_for_workspace(self, workspace: WorkspaceInfo) -> Dict[str, str]:
        """Return all env overrides for this workspace (workspace + venv if active)."""
        env = dict(workspace.env_overrides)
        venv_env = self.build_venv_env(workspace)
        env.update(venv_env)
        return env

    # ------------------------------------------------------------------
    # Resolve command for high-level actions
    # ------------------------------------------------------------------

    def resolve_command(
        self,
        action: str,
        workspace: Optional[WorkspaceInfo] = None,
    ) -> Optional[str]:
        """
        Resolve a high-level action (e.g. 'run_tests') to a shell command
        based on the active workspace's project type.
        """
        from edith.capabilities.terminal.terminal_models import COMMAND_TABLE

        ws = workspace or self.get_active_workspace()
        if not ws:
            return None

        table = COMMAND_TABLE.get(action, {})
        # Try each detected project type in order
        for ptype in ws.project_types:
            cmd = table.get(ptype)
            if cmd:
                return cmd

        return None


# Global singleton
workspace_manager = WorkspaceManager()
