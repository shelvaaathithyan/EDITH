import os
from pathlib import Path
from typing import List
from edith.capabilities.filesystem.filesystem_exceptions import (
    PathNotFoundError, ReadOnlyError, DuplicateNameError,
    InvalidPathError, DirectoryTraversalError, CircularMoveError,
    FileLockedError, UnsupportedExtensionError
)

class FilesystemValidator:
    """Pre-execution validation engine for filesystem operations."""
    
    INVALID_CHARS = '<>:"/\\|?*'
    
    @classmethod
    def validate_exists(cls, path: Path):
        if not path.exists():
            raise PathNotFoundError(f"Path does not exist: {path}")

    @classmethod
    def validate_not_exists(cls, path: Path):
        if path.exists():
            raise DuplicateNameError(f"Path already exists: {path}")

    @classmethod
    def validate_writable(cls, path: Path):
        cls.validate_exists(path)
        if not os.access(path, os.W_OK):
            raise ReadOnlyError(f"Path is read-only: {path}")

    @classmethod
    def validate_name(cls, name: str):
        # We only check the base name for invalid characters, not the full path
        for char in cls.INVALID_CHARS:
            if char in name:
                raise InvalidPathError(f"Invalid character '{char}' in name: {name}")

    @classmethod
    def validate_traversal(cls, base_path: Path, target_path: Path):
        """Ensure target_path resolves strictly inside base_path (prevent ../..)"""
        try:
            target_path.resolve().relative_to(base_path.resolve())
        except ValueError:
            raise DirectoryTraversalError(f"Target path {target_path} is outside allowed base {base_path}")

    @classmethod
    def validate_move(cls, src: Path, dst: Path):
        cls.validate_exists(src)
        # Prevent moving a folder into its own subfolder
        if src.is_dir() and dst.is_relative_to(src):
            raise CircularMoveError(f"Cannot move folder into itself: {src} -> {dst}")

    @classmethod
    def validate_lock(cls, path: Path):
        """Heuristically attempt to detect file locks."""
        if path.is_file():
            try:
                # Try opening it in append mode exclusively
                with open(path, 'a'):
                    pass
            except IOError:
                raise FileLockedError(f"File is locked by another process: {path}")

    @classmethod
    def validate_extension(cls, path: Path, allowed: List[str]):
        if path.suffix.lower() not in [ext.lower() for ext in allowed]:
            raise UnsupportedExtensionError(f"Unsupported extension {path.suffix}. Allowed: {allowed}")
