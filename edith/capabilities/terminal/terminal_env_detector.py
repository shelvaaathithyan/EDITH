"""
Terminal Capability — Environment Detector

Discovers installed developer tool versions by running each tool's
version command in a subprocess. Results are cached per workspace
and never re-run unless explicitly invalidated.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple

from edith.capabilities.terminal.terminal_models import EnvironmentInfo
from edith.utils.logger import logger


# ---------------------------------------------------------------------------
# Tool detection spec:
# (tool_id, executable, args, field_name_on_EnvironmentInfo, version_regex)
# ---------------------------------------------------------------------------

_TOOL_SPECS: List[Tuple[str, str, List[str], str, str]] = [
    ("python",  "python",   ["--version"],    "python_version",  r"Python\s+([\d.]+)"),
    ("python3", "python3",  ["--version"],    "python_version",  r"Python\s+([\d.]+)"),
    ("node",    "node",     ["-v"],           "node_version",    r"v([\d.]+)"),
    ("npm",     "npm",      ["-v"],           "npm_version",     r"([\d.]+)"),
    ("yarn",    "yarn",     ["-v"],           "yarn_version",    r"([\d.]+)"),
    ("pnpm",    "pnpm",     ["-v"],           "pnpm_version",    r"([\d.]+)"),
    ("git",     "git",      ["--version"],    "git_version",     r"git version ([\d.]+)"),
    ("docker",  "docker",   ["--version"],    "docker_version",  r"Docker version ([\d.]+)"),
    ("java",    "java",     ["-version"],     "java_version",    r'version "([\d._]+)"'),
    ("cargo",   "cargo",    ["--version"],    "cargo_version",   r"cargo ([\d.]+)"),
    ("go",      "go",       ["version"],      "go_version",      r"go([\d.]+)"),
    ("flutter", "flutter",  ["--version"],    "flutter_version", r"Flutter ([\d.]+)"),
    ("nvcc",    "nvcc",     ["--version"],    "cuda_version",    r"release ([\d.]+)"),
]


class EnvironmentDetector:
    """
    Runs tool version commands and returns a populated EnvironmentInfo.
    Uses a short timeout per tool to avoid hanging.
    """

    TIMEOUT_SECONDS = 5

    @classmethod
    def detect(cls, cwd: Optional[str] = None) -> EnvironmentInfo:
        """
        Probe all configured tools and return an EnvironmentInfo.
        cwd is passed so PATH-local tools (e.g. venv python) are detected correctly.
        """
        info = EnvironmentInfo()
        available: List[str] = []
        unavailable: List[str] = []

        seen_tools: Dict[str, bool] = {}  # track which field already set

        for tool_id, exe, args, field_name, pattern in _TOOL_SPECS:
            # Skip if executable not found on PATH (fast check)
            if not shutil.which(exe):
                if tool_id not in seen_tools:
                    unavailable.append(tool_id)
                    seen_tools[tool_id] = False
                continue

            if seen_tools.get(tool_id):
                # Already detected via another executable name (e.g. python / python3)
                continue

            version = cls._probe(exe, args, pattern, cwd)
            if version:
                object.__setattr__(info, field_name, version)
                available.append(tool_id)
                seen_tools[tool_id] = True
            else:
                unavailable.append(tool_id)
                seen_tools[tool_id] = False

        info.available_tools = list(dict.fromkeys(available))      # deduplicated
        info.unavailable_tools = list(dict.fromkeys(unavailable))  # deduplicated
        logger.info(
            f"EnvDetector: available={info.available_tools}, "
            f"unavailable={info.unavailable_tools}"
        )
        return info

    @classmethod
    def _probe(
        cls,
        exe: str,
        args: List[str],
        pattern: str,
        cwd: Optional[str],
    ) -> Optional[str]:
        try:
            result = subprocess.run(
                [exe] + args,
                capture_output=True,
                text=True,
                timeout=cls.TIMEOUT_SECONDS,
                cwd=cwd,
            )
            output = (result.stdout + result.stderr).strip()
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        except Exception as e:
            logger.debug(f"EnvDetector: unexpected error probing {exe}: {e}")
        return None
