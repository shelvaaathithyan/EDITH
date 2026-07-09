"""
Unit tests — WorkspaceManager, ProjectDetector, EnvDetector
"""

import json
import pytest
from pathlib import Path

from edith.capabilities.terminal.terminal_workspace import WorkspaceManager
from edith.capabilities.terminal.terminal_project_detector import ProjectDetector
from edith.capabilities.terminal.terminal_models import ProjectType, PackageManager
from edith.capabilities.terminal.terminal_exceptions import WorkspaceError


# ---------------------------------------------------------------------------
# ProjectDetector tests
# ---------------------------------------------------------------------------

class TestProjectDetector:
    def test_node_npm_detection(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name":"test"}')
        (tmp_path / "package-lock.json").write_text("{}")
        types, pm = ProjectDetector.detect(tmp_path)
        assert ProjectType.NODE in types
        assert pm == PackageManager.NPM

    def test_node_yarn_detection(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name":"test"}')
        (tmp_path / "yarn.lock").write_text("")
        types, pm = ProjectDetector.detect(tmp_path)
        assert ProjectType.NODE in types
        assert pm == PackageManager.YARN

    def test_node_pnpm_detection(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name":"test"}')
        (tmp_path / "pnpm-lock.yaml").write_text("")
        types, pm = ProjectDetector.detect(tmp_path)
        assert ProjectType.NODE in types
        assert pm == PackageManager.PNPM

    def test_python_requirements_detection(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("flask\nrequests\n")
        types, pm = ProjectDetector.detect(tmp_path)
        assert ProjectType.PYTHON in types
        assert pm == PackageManager.PIP

    def test_rust_detection(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text('[package]\nname = "myapp"')
        types, pm = ProjectDetector.detect(tmp_path)
        assert ProjectType.RUST in types
        assert pm == PackageManager.CARGO

    def test_java_maven_detection(self, tmp_path):
        (tmp_path / "pom.xml").write_text("<project/>")
        types, pm = ProjectDetector.detect(tmp_path)
        assert ProjectType.JAVA_MAVEN in types
        assert pm == PackageManager.MVN

    def test_flutter_detection(self, tmp_path):
        (tmp_path / "pubspec.yaml").write_text("name: my_app")
        types, pm = ProjectDetector.detect(tmp_path)
        assert ProjectType.FLUTTER in types
        assert pm == PackageManager.FLUTTER

    def test_monorepo_multi_type(self, tmp_path):
        """A directory with both package.json and requirements.txt is multi-type."""
        (tmp_path / "package.json").write_text('{"name":"test"}')
        (tmp_path / "requirements.txt").write_text("flask")
        types, _ = ProjectDetector.detect(tmp_path)
        assert ProjectType.NODE in types
        assert ProjectType.PYTHON in types

    def test_unknown_directory(self, tmp_path):
        types, pm = ProjectDetector.detect(tmp_path)
        assert ProjectType.UNKNOWN in types

    def test_git_root_detection(self, tmp_path):
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        result = ProjectDetector.find_git_root(tmp_path)
        assert result == str(tmp_path)

    def test_venv_detection(self, tmp_path):
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "pyvenv.cfg").write_text("[virtualenv]")
        result = ProjectDetector.find_venv(tmp_path)
        assert result == str(venv)

    def test_docker_compose_detection(self, tmp_path):
        (tmp_path / "docker-compose.yml").write_text("version: '3'")
        result = ProjectDetector.find_docker_compose(tmp_path)
        assert result is not None
        assert "docker-compose.yml" in result

    def test_packagemanager_from_package_json_field(self, tmp_path):
        data = {"name": "test", "packageManager": "pnpm@8.0.0"}
        (tmp_path / "package.json").write_text(json.dumps(data))
        types, pm = ProjectDetector.detect(tmp_path)
        assert pm == PackageManager.PNPM


# ---------------------------------------------------------------------------
# WorkspaceManager tests
# ---------------------------------------------------------------------------

class TestWorkspaceManager:
    def test_open_workspace(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name":"test"}')
        wm = WorkspaceManager()
        ws = wm.open_workspace(str(tmp_path), run_env_detection=False)

        assert ws.workspace_id is not None
        assert ws.root_path == str(tmp_path)
        assert ProjectType.NODE in ws.project_types

    def test_open_nonexistent_workspace_raises(self):
        wm = WorkspaceManager()
        with pytest.raises(WorkspaceError):
            wm.open_workspace("/nonexistent/path/xyz")

    def test_active_workspace_set_on_open(self, tmp_path):
        wm = WorkspaceManager()
        ws = wm.open_workspace(str(tmp_path), run_env_detection=False)
        active = wm.get_active_workspace()
        assert active is not None
        assert active.workspace_id == ws.workspace_id

    def test_switch_workspace(self, tmp_path):
        wm = WorkspaceManager()
        ws1 = wm.open_workspace(str(tmp_path), run_env_detection=False)
        tmp2 = tmp_path / "sub"
        tmp2.mkdir()
        ws2 = wm.open_workspace(str(tmp2), run_env_detection=False)

        wm.switch_workspace(ws1.workspace_id)
        assert wm.get_active_workspace().workspace_id == ws1.workspace_id

    def test_venv_env_injection(self, tmp_path):
        """Verify venv env vars are injected when workspace has a venv."""
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "pyvenv.cfg").write_text("[virtualenv]")

        wm = WorkspaceManager()
        ws = wm.open_workspace(str(tmp_path), run_env_detection=False)

        assert ws.venv_path is not None
        env = wm.build_venv_env(ws)
        assert "VIRTUAL_ENV" in env
        assert str(venv) in env["PATH"]
        assert env["PYTHONHOME"] == ""

    def test_resolve_command_node(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name":"test"}')
        wm = WorkspaceManager()
        ws = wm.open_workspace(str(tmp_path), run_env_detection=False)

        cmd = wm.resolve_command("run_tests", ws)
        assert cmd == "npm test"

    def test_resolve_command_python(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("flask")
        wm = WorkspaceManager()
        ws = wm.open_workspace(str(tmp_path), run_env_detection=False)

        cmd = wm.resolve_command("run_tests", ws)
        assert cmd == "pytest"

    def test_resolve_unknown_action_returns_none(self, tmp_path):
        wm = WorkspaceManager()
        ws = wm.open_workspace(str(tmp_path), run_env_detection=False)
        cmd = wm.resolve_command("nonexistent_action", ws)
        assert cmd is None
