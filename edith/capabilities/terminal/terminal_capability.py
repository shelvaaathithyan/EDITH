"""
Terminal Capability — BaseCapability Implementation

The central entry point for all terminal actions. Delegates to
TerminalController, WorkspaceManager, ProcessManager, and WorkflowManager.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from edith.sdk.capability import (
    BaseCapability,
    CapabilityManifest,
    CapabilityResult,
    CapabilityValidationError,
)
from edith.capabilities.terminal.terminal_manifest import MANIFEST
from edith.capabilities.terminal.terminal_controller import terminal_controller
from edith.capabilities.terminal.terminal_process_manager import process_manager
from edith.capabilities.terminal.terminal_workspace import workspace_manager
from edith.capabilities.terminal.terminal_workflow_manager import workflow_manager
from edith.capabilities.terminal.terminal_shell_profiles import shell_registry
from edith.capabilities.terminal.terminal_session import TerminalSession
from edith.capabilities.terminal.terminal_exceptions import (
    CommandBlockedError,
    ExecutableNotFoundError,
    SessionNotFoundError,
    WorkingDirectoryError,
    WorkspaceError,
)
from edith.capabilities.terminal.terminal_utils import format_duration
from edith.core.events import AppEvent, event_bus

logger = logging.getLogger(__name__)


class TerminalCapability(BaseCapability):

    def get_manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            id=MANIFEST["id"],
            name=MANIFEST["name"],
            version=MANIFEST["version"],
            author=MANIFEST["author"],
            description=MANIFEST["description"],
            supported_platforms=MANIFEST["supported_platforms"],
            dependencies=MANIFEST["dependencies"],
            supported_actions=MANIFEST["supported_actions"],
            risk_matrix=MANIFEST["risk_matrix"],
            required_permissions=MANIFEST["required_permissions"],
        )

    def _do_initialize(self) -> None:
        # Core execution
        self.register_action("run_command",          self._action_run_command)
        self.register_action("run_script",           self._action_run_script)
        # Workspace
        self.register_action("open_workspace",       self._action_open_workspace)
        self.register_action("set_working_directory",self._action_set_working_directory)
        self.register_action("switch_workspace",     self._action_switch_workspace)
        # Shell
        self.register_action("open_terminal",        self._action_open_terminal)
        # Process lifecycle
        self.register_action("stop_process",         self._action_stop_process)
        self.register_action("restart_process",      self._action_restart_process)
        self.register_action("kill_process",         self._action_kill_process)
        self.register_action("list_processes",       self._action_list_processes)
        # Interactive I/O
        self.register_action("send_input",           self._action_send_input)
        self.register_action("send_ctrl_c",          self._action_send_ctrl_c)
        self.register_action("send_ctrl_break",      self._action_send_ctrl_break)
        # Process groups
        self.register_action("create_process_group", self._action_create_process_group)
        self.register_action("stop_group",           self._action_stop_group)
        self.register_action("list_groups",          self._action_list_groups)
        # Developer commands (project-type-aware)
        self.register_action("install_dependencies", self._action_developer_command)
        self.register_action("run_tests",            self._action_developer_command)
        self.register_action("build_project",        self._action_developer_command)
        self.register_action("start_project",        self._action_developer_command)
        self.register_action("stop_project",         self._action_stop_project)
        self.register_action("lint",                 self._action_developer_command)
        self.register_action("format",               self._action_developer_command)
        self.register_action("clean",                self._action_developer_command)
        # Workflows
        self.register_action("deploy_project",       self._action_run_workflow)
        self.register_action("run_full_test_suite",  self._action_run_workflow)
        self.register_action("clean_and_rebuild",    self._action_run_workflow)
        self.register_action("start_dev_environment",self._action_run_workflow)
        # Environment
        self.register_action("activate_venv",        self._action_activate_venv)
        self.register_action("deactivate_venv",      self._action_deactivate_venv)
        self.register_action("detect_environment",   self._action_detect_environment)
        # Misc
        self.register_action("clear_terminal",       self._action_clear_terminal)
        self.register_action("get_session_output",   self._action_get_session_output)

    # -----------------------------------------------------------------------
    # Validation hook — convert terminal-specific exceptions to SDK exceptions
    # -----------------------------------------------------------------------

    def validate(self, action: str, args: Dict[str, Any]) -> None:
        super().validate(action, args)

    def _wrap_blocked(self, fn, *args, **kwargs) -> CapabilityResult:
        """Execute fn, converting terminal exceptions to CapabilityResult failures."""
        try:
            return fn(*args, **kwargs)
        except CommandBlockedError as e:
            return self._fail("run_command", f"🚫 Command blocked: {e}", risk_escalated=True)
        except ExecutableNotFoundError as e:
            return self._fail("run_command", str(e))
        except WorkingDirectoryError as e:
            return self._fail("run_command", str(e))
        except WorkspaceError as e:
            return self._fail("open_workspace", str(e))
        except SessionNotFoundError as e:
            return self._fail("stop_process", str(e))

    def _fail(self, action: str, message: str, risk_escalated: bool = False) -> CapabilityResult:
        return CapabilityResult(
            success=False,
            capability=self._manifest.id,
            action=action,
            message=message,
            metadata={"risk_escalated": risk_escalated},
        )

    def _ok(self, action: str, message: str, data: Dict = None) -> CapabilityResult:
        return CapabilityResult(
            success=True,
            capability=self._manifest.id,
            action=action,
            message=message,
            structured_data=data or {},
        )

    def _session_result(
        self,
        action: str,
        session: TerminalSession,
        message: str,
    ) -> CapabilityResult:
        return CapabilityResult(
            success=True,
            capability=self._manifest.id,
            action=action,
            message=message,
            structured_data=session.to_dict(),
        )

    # -----------------------------------------------------------------------
    # Action: run_command
    # -----------------------------------------------------------------------

    def _action_run_command(self, args: Dict[str, Any]) -> CapabilityResult:
        command = args.get("command") or args.get("cmd")
        if not command:
            raise CapabilityValidationError("'command' argument is required.")

        ctx_cwd = self.context.get("last_cwd")
        cwd = args.get("cwd") or args.get("path")
        shell_id = args.get("shell")
        group_id = args.get("group_id")

        def _run():
            session = terminal_controller.run_command(
                command=command,
                cwd=cwd,
                shell_id=shell_id,
                group_id=group_id,
                context_cwd=ctx_cwd,
            )
            self._update_session_context(session, command)
            return self._session_result(
                "run_command",
                session,
                f"Running: {command}",
            )

        return self._wrap_blocked(_run)

    # -----------------------------------------------------------------------
    # Action: run_script
    # -----------------------------------------------------------------------

    def _action_run_script(self, args: Dict[str, Any]) -> CapabilityResult:
        script_path = args.get("path")
        if not script_path:
            raise CapabilityValidationError("'path' argument is required.")

        from pathlib import Path
        p = Path(script_path)
        if not p.is_file():
            return self._fail("run_script", f"Script not found: {script_path}")

        # Determine interpreter
        suffix = p.suffix.lower()
        interpreters = {
            ".py": "python",
            ".js": "node",
            ".sh": "bash",
            ".ps1": "powershell",
            ".bat": "cmd /C",
        }
        interp = interpreters.get(suffix, "")
        command = f"{interp} {script_path}".strip() if interp else str(script_path)

        return self._action_run_command({**args, "command": command})

    # -----------------------------------------------------------------------
    # Action: open_workspace
    # -----------------------------------------------------------------------

    def _action_open_workspace(self, args: Dict[str, Any]) -> CapabilityResult:
        path = args.get("path")
        if not path:
            raise CapabilityValidationError("'path' argument is required.")

        def _open():
            workspace = workspace_manager.open_workspace(path)
            self.context.update({
                "last_cwd": workspace.root_path,
                "last_workspace_id": workspace.workspace_id,
                "project_type": workspace.project_types[0].value if workspace.project_types else "unknown",
            })
            types_str = ", ".join(t.value for t in workspace.project_types)
            tools_str = ", ".join(workspace.environment.available_tools[:5])
            msg = (
                f"Opened workspace: {workspace.name}\n"
                f"• Project: {types_str}\n"
                f"• Tools detected: {tools_str or 'none'}"
            )
            if workspace.git_root:
                msg += "\n• Git repository detected"
            if workspace.venv_path:
                msg += "\n• Python virtualenv detected"
            return self._ok("open_workspace", msg, workspace.model_dump())

        return self._wrap_blocked(_open)

    # -----------------------------------------------------------------------
    # Action: set_working_directory
    # -----------------------------------------------------------------------

    def _action_set_working_directory(self, args: Dict[str, Any]) -> CapabilityResult:
        path = args.get("path") or args.get("cwd")
        if not path:
            raise CapabilityValidationError("'path' argument is required.")

        from pathlib import Path
        resolved = Path(path).resolve()
        if not resolved.is_dir():
            return self._fail("set_working_directory", f"Directory not found: {path}")

        self.context.update({"last_cwd": str(resolved)})
        event_bus.publish(AppEvent.WORKING_DIRECTORY_CHANGED, {"cwd": str(resolved)})
        return self._ok("set_working_directory", f"Working directory: {resolved}")

    # -----------------------------------------------------------------------
    # Action: switch_workspace
    # -----------------------------------------------------------------------

    def _action_switch_workspace(self, args: Dict[str, Any]) -> CapabilityResult:
        workspace_id = args.get("workspace_id")
        if not workspace_id:
            raise CapabilityValidationError("'workspace_id' argument is required.")

        def _switch():
            ws = workspace_manager.switch_workspace(workspace_id)
            self.context.update({
                "last_cwd": ws.root_path,
                "last_workspace_id": ws.workspace_id,
            })
            return self._ok("switch_workspace", f"Switched to workspace: {ws.name}")

        return self._wrap_blocked(_switch)

    # -----------------------------------------------------------------------
    # Action: open_terminal
    # -----------------------------------------------------------------------

    def _action_open_terminal(self, args: Dict[str, Any]) -> CapabilityResult:
        shell_id = args.get("shell") or args.get("shell_id")
        cwd = args.get("cwd") or self.context.get("last_cwd")

        profile = shell_registry.resolve(shell_id)
        success = terminal_controller.open_terminal_window(
            shell_id=profile.id,
            cwd=cwd,
        )
        self.context.update({"last_shell": profile.id})
        if success:
            return self._ok("open_terminal", f"Opened {profile.display_name}")
        return self._fail("open_terminal", f"Failed to open {profile.display_name}")

    # -----------------------------------------------------------------------
    # Action: stop_process
    # -----------------------------------------------------------------------

    def _action_stop_process(self, args: Dict[str, Any]) -> CapabilityResult:
        session_id = args.get("session_id") or self.context.get("last_session_id")
        if not session_id:
            return self._fail("stop_process", "No active session to stop.")

        def _stop():
            success = terminal_controller.stop_session(session_id, force=False)
            msg = f"Process stopped." if success else f"Failed to stop process {session_id[:8]}."
            return self._ok("stop_process", msg, {"session_id": session_id}) if success else \
                   self._fail("stop_process", msg)

        return self._wrap_blocked(_stop)

    # -----------------------------------------------------------------------
    # Action: kill_process
    # -----------------------------------------------------------------------

    def _action_kill_process(self, args: Dict[str, Any]) -> CapabilityResult:
        session_id = args.get("session_id") or self.context.get("last_session_id")
        if not session_id:
            return self._fail("kill_process", "No active session to kill.")

        def _kill():
            success = terminal_controller.stop_session(session_id, force=True)
            msg = "Process force-killed." if success else f"Failed to kill {session_id[:8]}."
            return self._ok("kill_process", msg) if success else self._fail("kill_process", msg)

        return self._wrap_blocked(_kill)

    # -----------------------------------------------------------------------
    # Action: restart_process
    # -----------------------------------------------------------------------

    def _action_restart_process(self, args: Dict[str, Any]) -> CapabilityResult:
        session_id = args.get("session_id") or self.context.get("last_session_id")
        if not session_id:
            return self._fail("restart_process", "No active session to restart.")

        def _restart():
            new_session = terminal_controller.restart_session(session_id)
            self._update_session_context(new_session, new_session.command)
            return self._session_result("restart_process", new_session, "Process restarted.")

        return self._wrap_blocked(_restart)

    # -----------------------------------------------------------------------
    # Action: list_processes
    # -----------------------------------------------------------------------

    def _action_list_processes(self, args: Dict[str, Any]) -> CapabilityResult:
        running = process_manager.list_running()
        summaries = [s.to_dict() for s in running]
        msg = f"{len(running)} process{'es' if len(running) != 1 else ''} running."
        return self._ok("list_processes", msg, {"sessions": summaries})

    # -----------------------------------------------------------------------
    # Actions: send_input / send_ctrl_c / send_ctrl_break
    # -----------------------------------------------------------------------

    def _action_send_input(self, args: Dict[str, Any]) -> CapabilityResult:
        session_id = args.get("session_id") or self.context.get("last_session_id")
        text = args.get("text", "")
        if not session_id:
            return self._fail("send_input", "No active session to send input to.")

        success = process_manager.send_input(session_id, text)
        return self._ok("send_input", f"Sent: '{text}'") if success else \
               self._fail("send_input", "Failed to send input.")

    def _action_send_ctrl_c(self, args: Dict[str, Any]) -> CapabilityResult:
        session_id = args.get("session_id") or self.context.get("last_session_id")
        if not session_id:
            return self._fail("send_ctrl_c", "No active session.")
        success = terminal_controller.send_ctrl_c(session_id)
        return self._ok("send_ctrl_c", "Sent CTRL+C.") if success else \
               self._fail("send_ctrl_c", "Failed to send CTRL+C.")

    def _action_send_ctrl_break(self, args: Dict[str, Any]) -> CapabilityResult:
        session_id = args.get("session_id") or self.context.get("last_session_id")
        if not session_id:
            return self._fail("send_ctrl_break", "No active session.")
        success = process_manager.send_ctrl_break(session_id)
        return self._ok("send_ctrl_break", "Sent CTRL+BREAK.") if success else \
               self._fail("send_ctrl_break", "Failed to send CTRL+BREAK.")

    # -----------------------------------------------------------------------
    # Actions: process groups
    # -----------------------------------------------------------------------

    def _action_create_process_group(self, args: Dict[str, Any]) -> CapabilityResult:
        name = args.get("name", "Unnamed Group")
        group = process_manager.create_group(name)
        self.context.update({"last_group_id": group.group_id})
        return self._ok("create_process_group", f"Process group created: {name}",
                        {"group_id": group.group_id, "name": name})

    def _action_stop_group(self, args: Dict[str, Any]) -> CapabilityResult:
        group_id = args.get("group_id") or self.context.get("last_group_id")
        if not group_id:
            return self._fail("stop_group", "No active process group.")

        def _stop():
            results = process_manager.stop_group(group_id)
            stopped = sum(1 for r in results if r)
            return self._ok("stop_group", f"Stopped {stopped}/{len(results)} processes in group.")

        return self._wrap_blocked(_stop)

    def _action_list_groups(self, args: Dict[str, Any]) -> CapabilityResult:
        groups = process_manager.list_groups()
        data = [g.model_dump() for g in groups]
        return self._ok("list_groups", f"{len(groups)} process group(s).", {"groups": data})

    # -----------------------------------------------------------------------
    # Developer commands (project-type-aware)
    # -----------------------------------------------------------------------

    def _action_developer_command(self, args: Dict[str, Any]) -> CapabilityResult:
        """Routes install_dependencies, run_tests, build, lint, format, clean, etc."""
        action = args.get("action", "")
        workspace = workspace_manager.get_active_workspace()
        command = workspace_manager.resolve_command(action, workspace)

        if not command:
            project_type = (
                workspace.project_types[0].value if workspace and workspace.project_types
                else "unknown"
            )
            return self._fail(
                action,
                f"No command defined for '{action}' in a {project_type} project. "
                f"Try running the command manually.",
            )

        # Override cwd with workspace root
        run_args = dict(args)
        run_args["command"] = command
        if workspace:
            run_args.setdefault("cwd", workspace.root_path)

        return self._action_run_command(run_args)

    # -----------------------------------------------------------------------
    # Action: stop_project (stop all running sessions in workspace)
    # -----------------------------------------------------------------------

    def _action_stop_project(self, args: Dict[str, Any]) -> CapabilityResult:
        group_id = self.context.get("last_group_id")
        if group_id:
            return self._action_stop_group({"group_id": group_id})

        # Fallback: stop the last session
        return self._action_stop_process(args)

    # -----------------------------------------------------------------------
    # Workflow actions
    # -----------------------------------------------------------------------

    def _action_run_workflow(self, args: Dict[str, Any]) -> CapabilityResult:
        action = args.get("action", "")
        steps = workflow_manager.expand(action)
        if not steps:
            return self._fail(action, f"Workflow '{action}' has no steps to execute.")

        # Create a group for this workflow
        wf_def = workflow_manager.get(action)
        group = None
        if wf_def and wf_def.creates_group:
            group = process_manager.create_group(wf_def.display_name)
            self.context.update({"last_group_id": group.group_id})

        completed = 0
        for step in steps:
            if step.capability != "terminal":
                # Hand off to other capabilities via event bus
                logger.info(f"Workflow step delegated: {step.capability}.{step.action}")
                event_bus.publish(
                    AppEvent.WORKFLOW_STEP_COMPLETED,
                    {"step": step.action, "delegated_to": step.capability},
                )
                completed += 1
                continue

            step_args = dict(step.args)
            step_args["action"] = step.action
            if group:
                step_args["group_id"] = group.group_id

            # Route to the right action handler
            handler = self._actions.get(step.action)
            if handler:
                result = handler(step_args)
                if not result.success and step.on_failure == "stop":
                    event_bus.publish(AppEvent.WORKFLOW_FAILED, {"step": step.action})
                    return self._fail(action, f"Workflow failed at step: {step.label or step.action}")
            completed += 1
            event_bus.publish(AppEvent.WORKFLOW_STEP_COMPLETED, {"step": step.action})

        event_bus.publish(AppEvent.WORKFLOW_COMPLETED, {"workflow": action, "steps": completed})
        return self._ok(action, f"Workflow '{action}' completed ({completed} steps).")

    # -----------------------------------------------------------------------
    # Environment actions
    # -----------------------------------------------------------------------

    def _action_activate_venv(self, args: Dict[str, Any]) -> CapabilityResult:
        workspace = workspace_manager.get_active_workspace()
        if not workspace or not workspace.venv_path:
            return self._fail("activate_venv", "No virtualenv found in current workspace.")
        self.context.update({"active_venv": workspace.venv_path})
        return self._ok("activate_venv", f"Virtualenv activated: {workspace.venv_path}")

    def _action_deactivate_venv(self, args: Dict[str, Any]) -> CapabilityResult:
        self.context.update({"active_venv": ""})
        event_bus.publish(AppEvent.VENV_DEACTIVATED, {})
        return self._ok("deactivate_venv", "Virtualenv deactivated.")

    def _action_detect_environment(self, args: Dict[str, Any]) -> CapabilityResult:
        from edith.capabilities.terminal.terminal_env_detector import EnvironmentDetector
        cwd = self.context.get("last_cwd")
        env_info = EnvironmentDetector.detect(cwd=cwd)
        tools = ", ".join(env_info.available_tools) or "none"
        return self._ok(
            "detect_environment",
            f"Detected tools: {tools}",
            env_info.model_dump(),
        )

    # -----------------------------------------------------------------------
    # Misc actions
    # -----------------------------------------------------------------------

    def _action_clear_terminal(self, args: Dict[str, Any]) -> CapabilityResult:
        # Clears the output buffer of the last session
        session_id = args.get("session_id") or self.context.get("last_session_id")
        if session_id:
            session = process_manager.get_session(session_id)
            if session:
                session.output_lines.clear()
        return self._ok("clear_terminal", "Terminal cleared.")

    def _action_get_session_output(self, args: Dict[str, Any]) -> CapabilityResult:
        session_id = args.get("session_id") or self.context.get("last_session_id")
        if not session_id:
            return self._fail("get_session_output", "No session specified.")

        session = process_manager.get_session(session_id)
        if not session:
            return self._fail("get_session_output", f"Session {session_id[:8]} not found.")

        n = args.get("lines", 50)
        lines = session.get_last_output(n)
        text = "\n".join(ol.line for ol in lines)
        return self._ok(
            "get_session_output",
            f"Last {len(lines)} lines from session {session_id[:8]}:",
            {"output": text, "lines": [ol.model_dump() for ol in lines]},
        )

    # -----------------------------------------------------------------------
    # Context helper
    # -----------------------------------------------------------------------

    def _update_session_context(self, session: TerminalSession, command: str) -> None:
        """Persist session metadata into Interaction Context."""
        self.context.update({
            "last_session_id": session.session_id,
            "last_command": command,
            "last_cwd": session.cwd,
            "last_shell": session.shell_id,
        })

    # -----------------------------------------------------------------------
    # Shutdown
    # -----------------------------------------------------------------------

    def _do_shutdown(self) -> None:
        """Stop all running processes gracefully on shutdown."""
        running = process_manager.list_running()
        for session in running:
            try:
                process_manager.stop(session.session_id, force=False)
            except Exception as e:
                logger.warning(f"Could not stop session {session.session_id[:8]}: {e}")
        logger.info(f"TerminalCapability shutdown: stopped {len(running)} process(es).")
