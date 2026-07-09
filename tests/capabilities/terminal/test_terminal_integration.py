"""
Integration tests — Terminal Capability

Tests the four complete conversation flows from the spec:

1. Web dev workflow:  open_workspace → install_dependencies → start_project
2. Git workflow:      run_command(git status) → run_command(git pull) → run_tests
3. Stop & restart:   run_command → stop_process → restart_process
4. Process group:    create_group → run_command → stop_group
"""

import time
import sys
import pytest

from edith.ai.models import ResolvedExecutionPlan, ResolvedExecutionStep
from edith.capabilities.terminal.terminal_capability import TerminalCapability
from edith.capabilities.terminal.terminal_models import SessionStatus


def make_plan(action: str, **kwargs) -> ResolvedExecutionPlan:
    return ResolvedExecutionPlan(
        goal=action,
        steps=[ResolvedExecutionStep(
            tool="terminal",
            arguments={"action": action, **kwargs}
        )]
    )


def wait_for_session(cap, session_id: str, timeout: float = 10.0):
    from edith.capabilities.terminal.terminal_process_manager import process_manager
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = process_manager.get_session(session_id)
        if s and s.status != SessionStatus.RUNNING:
            return s
        time.sleep(0.1)
    return None


@pytest.fixture
def cap(monkeypatch):
    """Fresh TerminalCapability per test — avoids shared state."""
    from edith.interaction.context.context_manager import context_manager
    from edith.capabilities.terminal.terminal_shell_profiles import shell_registry
    from edith.capabilities.terminal.terminal_workspace import workspace_manager
    from edith.capabilities.terminal.terminal_process_manager import process_manager
    
    context_manager.store.clear()
    workspace_manager._workspaces.clear()
    workspace_manager._active_workspace_id = None
    
    # Clean up lingering processes from previous tests
    for session in process_manager.list_all():
        process_manager.stop(session.session_id, force=True)
    process_manager._sessions.clear()
    process_manager._groups.clear()
    
    # Force default shell to 'cmd' to prevent 'wt.exe' detaching GUI windows during tests
    monkeypatch.setattr(shell_registry, "WINDOWS_FALLBACK_CHAIN", ["cmd"])
    
    c = TerminalCapability()
    c.initialize()
    return c


class TestFlow1WebDev:
    """open_workspace → install (echoed) → start (echoed)"""

    def test_open_workspace_then_run_command(self, cap, tmp_path):
        # Step 1: open workspace
        r1 = cap.execute(make_plan("open_workspace", path=str(tmp_path)))
        assert r1.success, r1.message
        assert cap.context.get("last_cwd") == str(tmp_path)

        # Step 2: run a command — cwd should be inherited from workspace
        r2 = cap.execute(make_plan("run_command", command="echo npm_install_simulated"))
        assert r2.success, r2.message
        sid = r2.structured_data.get("session_id")
        assert sid is not None

        session = wait_for_session(cap, sid, timeout=8)
        assert session is not None
        assert session.status == SessionStatus.COMPLETED


class TestFlow2GitWorkflow:
    """git commands in sequence sharing cwd context"""

    def test_git_commands_share_cwd(self, cap, tmp_path):
        # Set working directory
        cap.execute(make_plan("set_working_directory", path=str(tmp_path)))
        assert cap.context.get("last_cwd") == str(tmp_path)

        # Run echo simulating git status (git may not be in test env)
        script = tmp_path / "git.py"
        script.write_text("print('git_status_ok')")
        r = cap.execute(make_plan("run_command", command=f'{sys.executable} {script}'))
        assert r.success
        sid = r.structured_data["session_id"]

        session = wait_for_session(cap, sid, timeout=8)
        assert session is not None
        # cwd should be the directory we set
        assert session.cwd == str(tmp_path)


class TestFlow3StopAndRestart:
    """start long-running → stop → restart"""

    def test_stop_and_restart_windows(self, cap, tmp_path):
        script = tmp_path / "sleep.py"
        script.write_text("import time\ntime.sleep(30)")
        cmd = 'ping 127.0.0.1 -n 30'
        r1 = cap.execute(make_plan("run_command", command=cmd, cwd=str(tmp_path)))
        assert r1.success
        time.sleep(0.4)
        
        sid = r1.structured_data["session_id"]
        from edith.capabilities.terminal.terminal_process_manager import process_manager
        print("\nBEFORE STOP:", process_manager.get_session(sid).status)

        # Stop it
        r2 = cap.execute(make_plan("stop_process"))
        assert r2.success, r2.message

        time.sleep(0.3)
        sid = r1.structured_data["session_id"]
        from edith.capabilities.terminal.terminal_process_manager import process_manager
        session = process_manager.get_session(sid)
        if session.status not in (SessionStatus.CANCELLED, SessionStatus.FAILED):
            print("\nOUTPUT 1:", [l.line for l in session.get_last_output()])
            print("\nSTATUS:", session.status)
        assert session.status in (SessionStatus.CANCELLED, SessionStatus.FAILED)

        # Restart (creates a new session with same command)
        r3 = cap.execute(make_plan("restart_process", session_id=sid))
        assert r3.success, r3.message
        new_sid = r3.structured_data["session_id"]
        assert new_sid != sid

        # Clean up
        cap.execute(make_plan("stop_process", session_id=new_sid))

    def test_run_command_and_stop(self, cap, tmp_path):
        """Cross-platform: echo a string, verify session completes."""
        r = cap.execute(make_plan("run_command", command="echo hello", cwd=str(tmp_path)))
        assert r.success
        sid = r.structured_data["session_id"]
        session = wait_for_session(cap, sid, timeout=8)
        assert session is not None


class TestFlow4ProcessGroups:
    """Create group, add processes, stop group"""

    def test_group_stop_all(self, cap, tmp_path):
        # Create group
        r1 = cap.execute(make_plan("create_process_group", name="test-app"))
        assert r1.success
        group_id = r1.structured_data["group_id"]

        script = tmp_path / "sleep.py"
        script.write_text("import time\ntime.sleep(30)")
        cmd = 'ping 127.0.0.1 -n 30'

        # Start 2 processes in the group
        r2 = cap.execute(make_plan("run_command", command=cmd, cwd=str(tmp_path), group_id=group_id))
        r3 = cap.execute(make_plan("run_command", command=cmd, cwd=str(tmp_path), group_id=group_id))
        time.sleep(0.4)
        assert r2.success
        assert r3.success

        # Stop the whole group
        r4 = cap.execute(make_plan("stop_group", group_id=group_id))
        assert r4.success, r4.message

        time.sleep(0.4)
        from edith.capabilities.terminal.terminal_process_manager import process_manager
        for sid in [r2.structured_data["session_id"], r3.structured_data["session_id"]]:
            s = process_manager.get_session(sid)
            if s.status not in (SessionStatus.CANCELLED, SessionStatus.FAILED):
                print("\nOUTPUT 2:", [l.line for l in s.get_last_output()])
            assert s.status in (SessionStatus.CANCELLED, SessionStatus.FAILED)


class TestBlockedCommands:
    """Verify dangerous commands return a failure result, not a crash."""

    @pytest.mark.parametrize("cmd", [
        "format C:",
        "del /f /s /q C:\\",
        "shutdown /s",
        "diskpart",
    ])
    def test_blocked_command_returns_failure(self, cap, cmd):
        r = cap.execute(make_plan("run_command", command=cmd))
        assert r.success is False
        assert "blocked" in r.message.lower() or "🚫" in r.message


class TestContextFlow:
    """Verify context keys are set and persisted between actions."""

    def test_context_chain(self, cap, tmp_path):
        cap.execute(make_plan("open_workspace", path=str(tmp_path)))
        assert cap.context.get("last_workspace_id") is not None

        cap.execute(make_plan("run_command", command="echo chain", cwd=str(tmp_path)))
        assert cap.context.get("last_session_id") is not None
        assert cap.context.get("last_command") == "echo chain"
        assert cap.context.get("last_cwd") == str(tmp_path)
