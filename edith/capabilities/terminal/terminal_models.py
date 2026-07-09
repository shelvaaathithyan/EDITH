"""
Terminal Capability — All typed data models and enums.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SessionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GroupStatus(str, Enum):
    RUNNING = "running"
    PARTIALLY_RUNNING = "partially_running"
    STOPPED = "stopped"


class StreamLevel(str, Enum):
    """Classification of each output line published to the Event Bus."""
    STDOUT = "stdout"       # Regular output
    STDERR = "stderr"       # Error stream (separate pipe)
    INFO = "info"           # Informational
    WARNING = "warning"     # Deprecation / warning keywords
    ERROR = "error"         # Error / exception keywords
    SUCCESS = "success"     # Done / passed / success keywords
    SYSTEM = "system"       # EDITH-generated metadata


class ProjectType(str, Enum):
    NODE = "node"
    PYTHON = "python"
    RUST = "rust"
    JAVA_MAVEN = "java_maven"
    JAVA_GRADLE = "java_gradle"
    GO = "go"
    CPP_CMAKE = "cpp_cmake"
    FLUTTER = "flutter"
    DOTNET = "dotnet"
    RUBY = "ruby"
    UNKNOWN = "unknown"


class PackageManager(str, Enum):
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    PIP = "pip"
    UV = "uv"
    POETRY = "poetry"
    CARGO = "cargo"
    MVN = "mvn"
    GRADLE = "gradle"
    GO = "go"
    FLUTTER = "flutter"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Output line
# ---------------------------------------------------------------------------

class OutputLine(BaseModel):
    """A single classified line of terminal output."""
    line: str
    level: StreamLevel = StreamLevel.STDOUT
    source: str = "stdout"          # "stdout" or "stderr"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ---------------------------------------------------------------------------
# Shell Profile
# ---------------------------------------------------------------------------

class ShellProfile(BaseModel):
    """Represents a fully configured shell execution profile."""
    id: str
    display_name: str
    executable: str
    args: List[str] = Field(default_factory=list)
    env_vars: Dict[str, str] = Field(default_factory=dict)
    icon: str = "terminal"
    visible_window: bool = False    # True = opens a separate visible window
    platform: str = "Windows"
    encoding: str = "utf-8"


# ---------------------------------------------------------------------------
# Process Group
# ---------------------------------------------------------------------------

class ProcessGroup(BaseModel):
    """Groups multiple sessions under a named logical unit."""
    group_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    session_ids: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: GroupStatus = GroupStatus.STOPPED


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------

class EnvironmentInfo(BaseModel):
    """Cached tool version discovery results for a workspace."""
    python_version: Optional[str] = None
    node_version: Optional[str] = None
    npm_version: Optional[str] = None
    yarn_version: Optional[str] = None
    pnpm_version: Optional[str] = None
    git_version: Optional[str] = None
    docker_version: Optional[str] = None
    java_version: Optional[str] = None
    cargo_version: Optional[str] = None
    go_version: Optional[str] = None
    flutter_version: Optional[str] = None
    cuda_version: Optional[str] = None
    available_tools: List[str] = Field(default_factory=list)
    unavailable_tools: List[str] = Field(default_factory=list)
    detected_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class WorkspaceInfo(BaseModel):
    """Full project context for a developer workspace."""
    workspace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    root_path: str
    project_types: List[ProjectType] = Field(default_factory=list)
    package_manager: Optional[PackageManager] = None
    git_root: Optional[str] = None
    venv_path: Optional[str] = None
    docker_compose_path: Optional[str] = None
    env_overrides: Dict[str, str] = Field(default_factory=dict)
    environment: EnvironmentInfo = Field(default_factory=EnvironmentInfo)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# ---------------------------------------------------------------------------
# Command resolution table
# ---------------------------------------------------------------------------

# Maps (action_name, project_type) → shell command string.
# Capabilities resolve high-level developer actions using this table.
COMMAND_TABLE: Dict[str, Dict[str, str]] = {
    "install_dependencies": {
        ProjectType.NODE: "npm install",
        ProjectType.PYTHON: "pip install -r requirements.txt",
        ProjectType.RUST: "cargo fetch",
        ProjectType.JAVA_MAVEN: "mvn dependency:resolve",
        ProjectType.JAVA_GRADLE: "gradle dependencies",
        ProjectType.GO: "go mod download",
        ProjectType.FLUTTER: "flutter pub get",
        ProjectType.DOTNET: "dotnet restore",
    },
    "run_tests": {
        ProjectType.NODE: "npm test",
        ProjectType.PYTHON: "pytest",
        ProjectType.RUST: "cargo test",
        ProjectType.JAVA_MAVEN: "mvn test",
        ProjectType.JAVA_GRADLE: "gradle test",
        ProjectType.GO: "go test ./...",
        ProjectType.FLUTTER: "flutter test",
        ProjectType.DOTNET: "dotnet test",
    },
    "build_project": {
        ProjectType.NODE: "npm run build",
        ProjectType.PYTHON: "python -m build",
        ProjectType.RUST: "cargo build --release",
        ProjectType.JAVA_MAVEN: "mvn package",
        ProjectType.JAVA_GRADLE: "gradle build",
        ProjectType.GO: "go build ./...",
        ProjectType.FLUTTER: "flutter build",
        ProjectType.DOTNET: "dotnet build",
    },
    "start_project": {
        ProjectType.NODE: "npm run dev",
        ProjectType.PYTHON: "python main.py",
        ProjectType.RUST: "cargo run",
        ProjectType.JAVA_MAVEN: "mvn spring-boot:run",
        ProjectType.GO: "go run .",
        ProjectType.FLUTTER: "flutter run",
        ProjectType.DOTNET: "dotnet run",
    },
    "lint": {
        ProjectType.NODE: "npm run lint",
        ProjectType.PYTHON: "ruff check .",
        ProjectType.RUST: "cargo clippy",
        ProjectType.GO: "golint ./...",
        ProjectType.FLUTTER: "flutter analyze",
        ProjectType.DOTNET: "dotnet format --verify-no-changes",
    },
    "format": {
        ProjectType.NODE: "npm run format",
        ProjectType.PYTHON: "ruff format .",
        ProjectType.RUST: "cargo fmt",
        ProjectType.GO: "gofmt -w .",
        ProjectType.FLUTTER: "dart format .",
        ProjectType.DOTNET: "dotnet format",
    },
    "clean": {
        ProjectType.NODE: "npm run clean",
        ProjectType.PYTHON: "find . -type d -name __pycache__ -exec rm -rf {} +",
        ProjectType.RUST: "cargo clean",
        ProjectType.JAVA_MAVEN: "mvn clean",
        ProjectType.JAVA_GRADLE: "gradle clean",
        ProjectType.GO: "go clean ./...",
        ProjectType.FLUTTER: "flutter clean",
        ProjectType.DOTNET: "dotnet clean",
    },
}
