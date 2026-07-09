"""
Terminal Capability — Shell Profile Registry

Data-driven shell profiles. New profiles can be added here or loaded from
a JSON config file without any code changes to the capability.
"""

from __future__ import annotations

import shutil
import sys
from typing import Dict, List, Optional

from edith.capabilities.terminal.terminal_models import ShellProfile
from edith.capabilities.terminal.terminal_exceptions import ShellNotFoundError
from edith.utils.logger import logger

# ---------------------------------------------------------------------------
# Built-in profile definitions
# ---------------------------------------------------------------------------

_BUILTIN_PROFILES: List[Dict] = [
    {
        "id": "powershell",
        "display_name": "PowerShell 7",
        "executable": "pwsh",
        "args": ["-NoLogo", "-NoProfile"],
        "icon": "powershell",
        "visible_window": False,
        "platform": "Windows",
        "encoding": "utf-8",
    },
    {
        "id": "powershell5",
        "display_name": "Windows PowerShell 5",
        "executable": "powershell",
        "args": ["-NoLogo", "-NoProfile"],
        "icon": "powershell",
        "visible_window": False,
        "platform": "Windows",
        "encoding": "cp1252",
    },
    {
        "id": "cmd",
        "display_name": "Command Prompt",
        "executable": "cmd",
        "args": ["/Q"],           # /Q suppresses echo
        "icon": "terminal",
        "visible_window": False,
        "platform": "Windows",
        "encoding": "cp1252",
    },
    {
        "id": "wt",
        "display_name": "Windows Terminal",
        "executable": "wt",
        "args": [],
        "icon": "terminal",
        "visible_window": True,   # wt always opens a window
        "platform": "Windows",
        "encoding": "utf-8",
    },
    {
        "id": "gitbash",
        "display_name": "Git Bash",
        "executable": "bash",
        "args": ["--login", "-i"],
        "icon": "git",
        "visible_window": False,
        "platform": "Windows",
        "encoding": "utf-8",
    },
    {
        "id": "wsl",
        "display_name": "WSL (Default Distro)",
        "executable": "wsl",
        "args": [],
        "icon": "linux",
        "visible_window": False,
        "platform": "Windows",
        "encoding": "utf-8",
    },
    {
        "id": "wsl-ubuntu",
        "display_name": "WSL Ubuntu",
        "executable": "wsl",
        "args": ["-d", "Ubuntu"],
        "icon": "ubuntu",
        "visible_window": False,
        "platform": "Windows",
        "encoding": "utf-8",
    },
    # POSIX shells
    {
        "id": "bash",
        "display_name": "Bash",
        "executable": "bash",
        "args": [],
        "icon": "terminal",
        "visible_window": False,
        "platform": "Linux",
        "encoding": "utf-8",
    },
    {
        "id": "zsh",
        "display_name": "Zsh",
        "executable": "zsh",
        "args": [],
        "icon": "terminal",
        "visible_window": False,
        "platform": "macOS",
        "encoding": "utf-8",
    },
]


class ShellProfileRegistry:
    """
    Resolves ShellProfile by ID, with fallback chain for Windows.
    New profiles can be registered at runtime.
    """

    # Windows fallback order: try each in sequence until one resolves
    WINDOWS_FALLBACK_CHAIN = ["wt", "powershell", "powershell5", "cmd"]
    LINUX_FALLBACK_CHAIN = ["bash", "sh"]
    MACOS_FALLBACK_CHAIN = ["zsh", "bash"]

    def __init__(self):
        self._profiles: Dict[str, ShellProfile] = {}
        self._load_builtins()

    def _load_builtins(self) -> None:
        for data in _BUILTIN_PROFILES:
            profile = ShellProfile(**data)
            self._profiles[profile.id] = profile

    def register(self, profile: ShellProfile) -> None:
        """Register a custom shell profile at runtime."""
        self._profiles[profile.id] = profile
        logger.info(f"Registered shell profile: {profile.id} ({profile.display_name})")

    def get(self, profile_id: str) -> Optional[ShellProfile]:
        """Retrieve a profile by ID. Returns None if not found."""
        return self._profiles.get(profile_id)

    def resolve(self, profile_id: Optional[str] = None) -> ShellProfile:
        """
        Resolve a shell profile by ID, with platform-aware fallback chain.
        Raises ShellNotFoundError if no usable shell is found.
        """
        if profile_id:
            profile = self._profiles.get(profile_id)
            if profile and self._is_available(profile):
                return profile
            # Requested profile not available, try fallback
            logger.warning(
                f"Shell profile '{profile_id}' not available. "
                f"Falling back to platform default."
            )

        # Platform fallback
        chain = self._get_fallback_chain()
        for fid in chain:
            p = self._profiles.get(fid)
            if p and self._is_available(p):
                logger.info(f"Using shell: {p.display_name} ({p.executable})")
                return p

        raise ShellNotFoundError(profile_id or "default")

    def get_default(self) -> ShellProfile:
        """Returns the platform default shell."""
        return self.resolve(None)

    def list_available(self) -> List[ShellProfile]:
        """Returns all profiles whose executable is present on PATH."""
        return [p for p in self._profiles.values() if self._is_available(p)]

    def _is_available(self, profile: ShellProfile) -> bool:
        return shutil.which(profile.executable) is not None

    def _get_fallback_chain(self) -> List[str]:
        if sys.platform == "win32":
            return self.WINDOWS_FALLBACK_CHAIN
        elif sys.platform == "darwin":
            return self.MACOS_FALLBACK_CHAIN
        return self.LINUX_FALLBACK_CHAIN


# Global registry instance
shell_registry = ShellProfileRegistry()
