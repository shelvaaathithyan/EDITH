"""
Unit tests — TerminalCapability manifest and context updates
"""

import pytest
from edith.capabilities.terminal.terminal_manifest import MANIFEST
from edith.capabilities.terminal.terminal_capability import TerminalCapability
from edith.sdk.capability import CapabilityManifest
from edith.permission.permission_models import RiskLevel


class TestManifest:
    @pytest.fixture(autouse=True)
    def cap(self):
        self.cap = TerminalCapability()
        self.cap.initialize()

    def test_manifest_id(self):
        assert self._manifest().id == "terminal"

    def test_manifest_has_all_actions(self):
        manifest_actions = set(self._manifest().supported_actions)
        registered_actions = set(self.cap._actions.keys())
        # Every registered action must appear in the manifest
        for action in registered_actions:
            assert action in manifest_actions, \
                f"Action '{action}' is registered but not listed in manifest"

    def test_risk_matrix_coverage(self):
        """Every supported_action should have a risk entry."""
        manifest = self._manifest()
        for action in manifest.supported_actions:
            assert action in manifest.risk_matrix, \
                f"Action '{action}' missing from risk_matrix"

    def test_high_risk_actions(self):
        manifest = self._manifest()
        assert manifest.risk_matrix["kill_process"] == RiskLevel.HIGH
        assert manifest.risk_matrix["run_script"] == RiskLevel.HIGH

    def test_low_risk_actions(self):
        manifest = self._manifest()
        assert manifest.risk_matrix["open_terminal"] == RiskLevel.LOW
        assert manifest.risk_matrix["run_tests"] == RiskLevel.LOW
        assert manifest.risk_matrix["list_processes"] == RiskLevel.LOW

    def test_manifest_returns_capability_manifest_type(self):
        m = self.cap.get_manifest()
        assert isinstance(m, CapabilityManifest)

    def _manifest(self):
        return self.cap.get_manifest()


class TestContextUpdates:
    """Verify that actions correctly write into Interaction Context."""

    @pytest.fixture(autouse=True)
    def setup(self):
        # Use a fresh capability instance with a real context
        self.cap = TerminalCapability()
        self.cap.initialize()

    def test_set_working_directory_updates_context(self, tmp_path):
        from edith.ai.models import ResolvedExecutionPlan, ResolvedExecutionStep
        plan = ResolvedExecutionPlan(
            goal="Set cwd",
            steps=[ResolvedExecutionStep(
                tool="terminal",
                arguments={"action": "set_working_directory", "path": str(tmp_path)}
            )]
        )
        result = self.cap.execute(plan)
        assert result.success is True
        assert self.cap.context.get("last_cwd") == str(tmp_path)

    def test_open_workspace_updates_context(self, tmp_path):
        from edith.ai.models import ResolvedExecutionPlan, ResolvedExecutionStep
        plan = ResolvedExecutionPlan(
            goal="Open workspace",
            steps=[ResolvedExecutionStep(
                tool="terminal",
                arguments={"action": "open_workspace", "path": str(tmp_path)}
            )]
        )
        result = self.cap.execute(plan)
        assert result.success is True
        assert self.cap.context.get("last_cwd") == str(tmp_path)
        assert self.cap.context.get("last_workspace_id") is not None

    def test_run_command_updates_last_session(self, tmp_path):
        from edith.ai.models import ResolvedExecutionPlan, ResolvedExecutionStep
        plan = ResolvedExecutionPlan(
            goal="Run echo",
            steps=[ResolvedExecutionStep(
                tool="terminal",
                arguments={"action": "run_command", "command": "echo hello", "cwd": str(tmp_path)}
            )]
        )
        result = self.cap.execute(plan)
        assert result.success is True
        assert self.cap.context.get("last_session_id") is not None
        assert self.cap.context.get("last_command") == "echo hello"
