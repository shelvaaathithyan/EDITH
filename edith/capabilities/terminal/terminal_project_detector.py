"""
Terminal Capability — Project Type Detector

Scans a directory for marker files and returns detected ProjectTypes
and the most likely PackageManager. Supports multi-type detection
(e.g., a monorepo with both Node and Python components).
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from edith.capabilities.terminal.terminal_models import PackageManager, ProjectType
from edith.utils.logger import logger


# ---------------------------------------------------------------------------
# Detection rules
# Each rule: (marker_filename, project_type, package_manager_or_None)
# ---------------------------------------------------------------------------

_DETECTION_RULES: List[Tuple[str, ProjectType, Optional[PackageManager]]] = [
    # Node / JS
    ("package.json",        ProjectType.NODE,         None),          # PM resolved separately
    # Python
    ("requirements.txt",    ProjectType.PYTHON,       PackageManager.PIP),
    ("pyproject.toml",      ProjectType.PYTHON,       None),          # PM resolved separately
    ("setup.py",            ProjectType.PYTHON,       PackageManager.PIP),
    ("setup.cfg",           ProjectType.PYTHON,       PackageManager.PIP),
    # Rust
    ("Cargo.toml",          ProjectType.RUST,         PackageManager.CARGO),
    # Java
    ("pom.xml",             ProjectType.JAVA_MAVEN,   PackageManager.MVN),
    ("build.gradle",        ProjectType.JAVA_GRADLE,  PackageManager.GRADLE),
    ("build.gradle.kts",    ProjectType.JAVA_GRADLE,  PackageManager.GRADLE),
    # Go
    ("go.mod",              ProjectType.GO,           PackageManager.GO),
    # C++ / CMake
    ("CMakeLists.txt",      ProjectType.CPP_CMAKE,    None),
    # Flutter / Dart
    ("pubspec.yaml",        ProjectType.FLUTTER,      PackageManager.FLUTTER),
    # .NET
    ("*.csproj",            ProjectType.DOTNET,       None),          # glob matched
    ("*.fsproj",            ProjectType.DOTNET,       None),
    # Ruby
    ("Gemfile",             ProjectType.RUBY,         None),
]

_NODE_PM_MARKERS = {
    "yarn.lock":         PackageManager.YARN,
    "pnpm-lock.yaml":    PackageManager.PNPM,
    "package-lock.json": PackageManager.NPM,
    "bun.lockb":         PackageManager.NPM,   # treat bun as npm-compatible for now
}

_PYTHON_PM_MARKERS = {
    "uv.lock":           PackageManager.UV,
    "poetry.lock":       PackageManager.POETRY,
}


class ProjectDetector:
    """
    Scans a root directory and returns all detected ProjectTypes
    along with the primary PackageManager.
    """

    @staticmethod
    def detect(root: Path) -> Tuple[List[ProjectType], Optional[PackageManager]]:
        """
        Returns (project_types, package_manager).
        project_types may contain multiple entries for monorepos.
        package_manager is the most specific one found.
        """
        if not root.is_dir():
            logger.warning(f"ProjectDetector: '{root}' is not a directory.")
            return [ProjectType.UNKNOWN], None

        detected_types: List[ProjectType] = []
        detected_pm: Optional[PackageManager] = None

        for marker, proj_type, pm in _DETECTION_RULES:
            if "*" in marker:
                # Glob pattern match
                matches = list(root.glob(marker))
                found = len(matches) > 0
            else:
                found = (root / marker).exists()

            if found and proj_type not in detected_types:
                detected_types.append(proj_type)
                if pm and not detected_pm:
                    detected_pm = pm

        # Resolve Node package manager more specifically
        if ProjectType.NODE in detected_types and not detected_pm:
            detected_pm = ProjectDetector._detect_node_pm(root)

        # Resolve Python package manager more specifically
        if ProjectType.PYTHON in detected_types and detected_pm in (
            PackageManager.PIP, None
        ):
            python_pm = ProjectDetector._detect_python_pm(root)
            if python_pm:
                detected_pm = python_pm

        # Resolve pyproject.toml based PM
        if ProjectType.PYTHON in detected_types and detected_pm is None:
            detected_pm = ProjectDetector._detect_python_pm(root) or PackageManager.PIP

        if not detected_types:
            detected_types = [ProjectType.UNKNOWN]

        logger.debug(
            f"ProjectDetector: {root.name} → types={[t.value for t in detected_types]}, "
            f"pm={detected_pm.value if detected_pm else None}"
        )
        return detected_types, detected_pm

    @staticmethod
    def _detect_node_pm(root: Path) -> PackageManager:
        for lockfile, pm in _NODE_PM_MARKERS.items():
            if (root / lockfile).exists():
                return pm

        # Check package.json for packageManager field
        pkg_json = root / "package.json"
        if pkg_json.exists():
            try:
                import json
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                pm_field = data.get("packageManager", "")
                if pm_field.startswith("yarn"):
                    return PackageManager.YARN
                if pm_field.startswith("pnpm"):
                    return PackageManager.PNPM
            except Exception:
                pass

        return PackageManager.NPM  # default

    @staticmethod
    def _detect_python_pm(root: Path) -> Optional[PackageManager]:
        for lockfile, pm in _PYTHON_PM_MARKERS.items():
            if (root / lockfile).exists():
                return pm

        # Check pyproject.toml for build system
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8")
                if "poetry" in content.lower():
                    return PackageManager.POETRY
                if "uv" in content.lower():
                    return PackageManager.UV
            except Exception:
                pass

        return None

    @staticmethod
    def find_git_root(path: Path) -> Optional[str]:
        """Walk up from path to find the nearest .git directory."""
        current = path if path.is_dir() else path.parent
        for parent in [current, *current.parents]:
            if (parent / ".git").exists():
                return str(parent)
        return None

    @staticmethod
    def find_venv(root: Path) -> Optional[str]:
        """Check common venv directory names at the project root."""
        candidates = [".venv", "venv", "env", ".env"]
        for name in candidates:
            p = root / name
            # A real venv contains pyvenv.cfg
            if p.is_dir() and (p / "pyvenv.cfg").exists():
                return str(p)
        return None

    @staticmethod
    def find_docker_compose(root: Path) -> Optional[str]:
        """Check for docker-compose files at the project root."""
        candidates = [
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        ]
        for name in candidates:
            p = root / name
            if p.exists():
                return str(p)
        return None
