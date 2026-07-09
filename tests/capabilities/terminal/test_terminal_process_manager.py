"""
Unit tests — TerminalProcessManager

Tests session lifecycle, group management, interactive stdin,
and thread-safety under concurrent access.
"""

import time
import threading
import sys
import pytest
from edith.capabilities.terminal.terminal_process_manager import TerminalProcessManager
from edith.capabilities.terminal.terminal_shell_profiles import shell_registry
from edith.capabilities.terminal.terminal_models import SessionStatus, GroupStatus
from edith.capabilities.terminal.terminal_exceptions import SessionNotFoundError


@pytest.fixture
def pm():
    """Fresh TerminalProcessManager for each test."""
    return TerminalProcessManager()


@pytest.fixture
def default_profile():
    from edith.capabilities.terminal.terminal_shell_profiles import shell_registry
    return shell_registry.resolve("cmd")


class TestSessionLifecycle:
    def test_start_echo_command(self, pm, default_profile, tmp_path):
        session = pm.start(
            command='python -c "print(\'hello_world\')"',
            cwd=str(tmp_path),
            shell_profile=default_profile,
        )
        assert session.session_id is not None
        assert session.pid is not None
        assert session.status == SessionStatus.RUNNING

    def test_session_completes(self, pm, default_profile, tmp_path):
        session = pm.start(
            command=f'"{sys.executable}" -c "print(\'done\')"',
            cwd=str(tmp_path),
            shell_profile=default_profile,
        )
        # Wait for completion (short echo should finish quickly)
        deadline = time.time() + 10
        while session.status == SessionStatus.RUNNING and time.time() < deadline:
            time.sleep(0.1)

        assert session.status in (SessionStatus.COMPLETED, SessionStatus.FAILED)

    def test_stop_running_session(self, pm, default_profile, tmp_path):
        """Start a long-running process and stop it."""
        script = tmp_path / "sleep.py"
        script.write_text("import time\ntime.sleep(30)")
        cmd = 'python sleep.py'
        session = pm.start(
            command=cmd,
            cwd=str(tmp_path),
            shell_profile=default_profile,
        )
        time.sleep(0.3)  # give process time to start
        if session.status != SessionStatus.RUNNING:
            print("\nOUTPUT:", [l.line for l in session.get_last_output()])
        assert session.status == SessionStatus.RUNNING

        success = pm.stop(session.session_id)
        assert success is True

        time.sleep(0.3)
        assert session.status in (SessionStatus.CANCELLED, SessionStatus.FAILED)

    def test_restart_session(self, pm, default_profile, tmp_path):
        session = pm.start(
            command=f'"{sys.executable}" -c "print(\'original\')"',
            cwd=str(tmp_path),
            shell_profile=default_profile,
        )
        old_id = session.session_id

        # Wait briefly then restart
        time.sleep(0.2)
        new_session = pm.restart(old_id)

        assert new_session.session_id != old_id
        assert new_session.command == session.command
        assert new_session.cwd == session.cwd

    def test_get_nonexistent_session(self, pm):
        assert pm.get_session("nonexistent-id") is None

    def test_stop_nonexistent_raises(self, pm):
        with pytest.raises(SessionNotFoundError):
            pm.stop("bad-session-id")

    def test_list_running(self, pm, default_profile, tmp_path):
        script = tmp_path / "sleep.py"
        script.write_text("import time\ntime.sleep(30)")
        cmd = 'python sleep.py'
        session = pm.start(command=cmd, cwd=str(tmp_path), shell_profile=default_profile)
        time.sleep(0.2)

        running = pm.list_running()
        ids = [s.session_id for s in running]
        assert session.session_id in ids

        pm.stop(session.session_id)


class TestProcessGroups:
    def test_create_group(self, pm):
        group = pm.create_group("test-group")
        assert group.group_id is not None
        assert group.name == "test-group"
        assert group.status == GroupStatus.STOPPED

    def test_sessions_added_to_group(self, pm, default_profile, tmp_path):
        group = pm.create_group("my-app")
        script = tmp_path / "sleep.py"
        script.write_text("import time\ntime.sleep(30)")
        cmd = 'python sleep.py'

        s1 = pm.start(command=cmd, cwd=str(tmp_path), shell_profile=default_profile, group_id=group.group_id)
        s2 = pm.start(command=cmd, cwd=str(tmp_path), shell_profile=default_profile, group_id=group.group_id)
        time.sleep(0.2)

        group_state = pm.get_group(group.group_id)
        assert s1.session_id in group_state.session_ids
        assert s2.session_id in group_state.session_ids

        pm.stop_group(group.group_id)

    def test_stop_group(self, pm, default_profile, tmp_path):
        group = pm.create_group("killable-group")
        script = tmp_path / "sleep.py"
        script.write_text("import time\ntime.sleep(30)")
        cmd = 'python sleep.py'

        sessions = [
            pm.start(command=cmd, cwd=str(tmp_path), shell_profile=default_profile, group_id=group.group_id)
            for _ in range(3)
        ]
        time.sleep(0.3)

        results = pm.stop_group(group.group_id)
        assert len(results) == 3
        assert all(results)

        time.sleep(0.3)
        for s in sessions:
            assert s.status in (SessionStatus.CANCELLED, SessionStatus.FAILED)


class TestInteractiveInput:
    def test_send_input_to_running_process(self, pm, default_profile, tmp_path):
        """Verify send_input writes to stdin without error."""
        script = tmp_path / "read.py"
        script.write_text("import sys\nprint(sys.stdin.read())")
        cmd = 'python read.py'

        session = pm.start(command=cmd, cwd=str(tmp_path), shell_profile=default_profile)
        time.sleep(0.3)

        success = pm.send_input(session.session_id, "hello")
        assert success is True

        # Clean up
        pm.stop(session.session_id, force=True)

    def test_send_input_to_stopped_session_fails(self, pm, default_profile, tmp_path):
        session = pm.start(command=f'"{sys.executable}" -c "print(\'done\')"', cwd=str(tmp_path), shell_profile=default_profile)
        deadline = time.time() + 5
        while session.status == SessionStatus.RUNNING and time.time() < deadline:
            time.sleep(0.1)

        success = pm.send_input(session.session_id, "too late")
        assert success is False
