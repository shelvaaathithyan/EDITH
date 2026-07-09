"""
Terminal Capability — Command Validator

Performs security validation before any command reaches the process manager.
The validator runs BEFORE the Permission Manager, so blocked commands are
caught early and escalated to CRITICAL risk.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import List, Optional

from edith.capabilities.terminal.terminal_exceptions import (
    CommandBlockedError,
    ExecutableNotFoundError,
    WorkingDirectoryError,
)
from edith.utils.logger import logger


# ---------------------------------------------------------------------------
# Block-list patterns
# Each tuple: (display_name, compiled_regex)
# Matched case-insensitively against the full command string (stripped).
# ---------------------------------------------------------------------------

_BLOCK_LIST: List[tuple[str, re.Pattern]] = [
    # Windows destructive commands
    ("del /f /s /q",         re.compile(r"\bdel\s+.*(/f|/s|/q)", re.IGNORECASE)),
    ("rd /s /q",             re.compile(r"\brd\s+.*(/s|/q)", re.IGNORECASE)),
    ("rmdir /s",             re.compile(r"\brmdir\s+.*/s", re.IGNORECASE)),
    ("format drive",         re.compile(r"\bformat\s+[a-z]:", re.IGNORECASE)),
    ("shutdown",             re.compile(r"\bshutdown\b\s*/[srft]", re.IGNORECASE)),
    ("taskkill /f",          re.compile(r"\btaskkill\s+.*/f", re.IGNORECASE)),
    ("reg delete",           re.compile(r"\breg\s+delete\b", re.IGNORECASE)),
    ("reg add",              re.compile(r"\breg\s+add\b", re.IGNORECASE)),
    ("diskpart",             re.compile(r"\bdiskpart\b", re.IGNORECASE)),
    ("net user /add",        re.compile(r"\bnet\s+user\b.*(/add)", re.IGNORECASE)),
    ("net localgroup admins",re.compile(r"\bnet\s+localgroup\b.*administrators\b.*(/add)", re.IGNORECASE)),
    ("Set-ExecutionPolicy",  re.compile(r"\bSet-ExecutionPolicy\b", re.IGNORECASE)),
    ("Invoke-Expression",    re.compile(r"\bIEX\b|\bInvoke-Expression\b", re.IGNORECASE)),
    # POSIX destructive commands
    ("rm -rf /",             re.compile(r"\brm\b\s+(-[^-]*r[^-]*f|-[^-]*f[^-]*r|--force\s+--recursive|--recursive\s+--force)\s+/", re.IGNORECASE)),
    ("rm -rf ~",             re.compile(r"\brm\b\s+(-[^-]*r[^-]*f|-[^-]*f[^-]*r).*~", re.IGNORECASE)),
    ("mkfs",                 re.compile(r"\bmkfs\b", re.IGNORECASE)),
    ("dd if=/dev/zero",      re.compile(r"\bdd\b.*if=/dev/zero", re.IGNORECASE)),
    ("> /dev/sda",           re.compile(r">\s*/dev/sd[a-z]", re.IGNORECASE)),
    ("chmod -R 777 /",       re.compile(r"\bchmod\b.*-R.*777.*/", re.IGNORECASE)),
    ("curl | bash",          re.compile(r"\bcurl\b.+\|\s*(ba)?sh", re.IGNORECASE)),
    ("wget | bash",          re.compile(r"\bwget\b.+\|\s*(ba)?sh", re.IGNORECASE)),
]


class TerminalValidator:
    """
    Validates terminal commands before execution.
    Raises typed exceptions on failure so the caller can decide risk level.
    """

    @staticmethod
    def validate_command(command: str) -> None:
        """
        Full validation pipeline:
        1. Check block-list (CommandBlockedError → CRITICAL)
        2. Check executable exists (ExecutableNotFoundError → validation error)

        Does NOT check cwd here — that happens in validate_working_directory.
        """
        command = command.strip()
        if not command:
            raise ValueError("Command cannot be empty.")

        TerminalValidator._check_block_list(command)
        TerminalValidator._check_executable(command)

    @staticmethod
    def validate_working_directory(cwd: str) -> None:
        """
        Ensure the working directory exists and is accessible.
        Raises WorkingDirectoryError if not.
        """
        path = Path(cwd)
        if not path.exists():
            raise WorkingDirectoryError(cwd, "does not exist")
        if not path.is_dir():
            raise WorkingDirectoryError(cwd, "is not a directory")

    @staticmethod
    def _check_block_list(command: str) -> None:
        for name, pattern in _BLOCK_LIST:
            if pattern.search(command):
                logger.warning(f"BLOCKED command: '{command}' matched pattern '{name}'")
                raise CommandBlockedError(command, name)

    @staticmethod
    def _check_executable(command: str) -> None:
        """
        Extract the base executable from the command and verify it exists on PATH.
        Skips check for built-in shell commands that are not standalone executables.
        """
        # Built-in shell commands that don't exist as standalone executables
        _SHELL_BUILTINS = {
            "echo", "set", "export", "cd", "pushd", "popd", "dir", "type",
            "cls", "clear", "exit", "pause", "rem", "if", "for", "while",
            "do", "then", "fi", "else", "elif", "case", "in", "esac",
        }

        parts = command.split()
        if not parts:
            return

        exe = parts[0]

        # Strip any path prefix — only validate the executable name
        exe_name = Path(exe).name

        # Skip builtins
        if exe_name.lower() in _SHELL_BUILTINS:
            return

        # Skip if it looks like a full path that exists
        if Path(exe).is_file():
            return

        # Skip compound shell syntax starters
        if exe in ("&&", "||", ";", "|", "source", ".", "eval"):
            return

        # Check PATH
        if shutil.which(exe_name) is None:
            # Soft check: only raise if it looks like a real executable (not a shell builtin alias)
            logger.debug(f"Validator: '{exe_name}' not found on PATH (may be shell builtin or typo)")
            # We raise only if it doesn't look like a built-in or relative command
            if not exe.startswith(".") and "/" not in exe and "\\" not in exe:
                raise ExecutableNotFoundError(exe_name)
