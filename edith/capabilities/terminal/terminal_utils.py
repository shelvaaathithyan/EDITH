"""
Terminal Capability — Utility Functions

Path resolution, environment variable helpers, and command parsing.
"""

from __future__ import annotations

import os
import re
import shlex
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def resolve_cwd(
    explicit_path: Optional[str],
    context_cwd: Optional[str],
    workspace_root: Optional[str] = None,
) -> str:
    """
    Resolve the working directory using precedence:
    1. Explicit path argument
    2. Active workspace root
    3. Interaction context last_cwd
    4. User home directory
    """
    candidates = [explicit_path, workspace_root, context_cwd]
    for candidate in candidates:
        if candidate:
            p = Path(candidate).resolve()
            if p.is_dir():
                return str(p)
    return str(Path.home())


def expand_path(path: str) -> str:
    """Expand ~ and environment variables in a path string."""
    return str(Path(os.path.expandvars(os.path.expanduser(path))).resolve())


def extract_executable(command: str) -> str:
    """
    Returns the executable name from a command string.
    e.g. 'npm run dev --port 3000' → 'npm'
    """
    command = command.strip()
    if not command:
        return ""
    parts = shlex.split(command) if sys.platform != "win32" else command.split()
    return Path(parts[0]).name if parts else ""


def inject_venv_env(
    base_env: Dict[str, str],
    venv_path: str,
) -> Dict[str, str]:
    """
    Return a copy of base_env with the virtualenv's scripts directory
    injected at the front of PATH.
    """
    env = dict(base_env)
    venv = Path(venv_path)
    scripts = venv / ("Scripts" if sys.platform == "win32" else "bin")
    env["VIRTUAL_ENV"] = str(venv)
    env["PATH"] = str(scripts) + os.pathsep + env.get("PATH", "")
    env["PYTHONHOME"] = ""
    return env


def format_duration(seconds: float) -> str:
    """Human-readable duration string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.0f}s"


def truncate_command(command: str, max_len: int = 60) -> str:
    """Truncate a command string for display."""
    return command[:max_len] + "..." if len(command) > max_len else command


def parse_npm_script(package_json_path: str, script_name: str) -> Optional[str]:
    """
    Reads package.json and returns the raw script command for a given name.
    Returns None if script not found or file unreadable.
    """
    try:
        import json
        data = json.loads(Path(package_json_path).read_text(encoding="utf-8"))
        return data.get("scripts", {}).get(script_name)
    except Exception:
        return None


def detect_encoding(profile_id: str) -> str:
    """
    Returns the expected encoding for a given shell profile ID.
    Windows legacy shells use cp1252; modern shells use utf-8.
    """
    legacy = {"cmd", "powershell5"}
    return "cp1252" if profile_id in legacy else "utf-8"
