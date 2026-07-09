class FilesystemException(Exception):
    """Base exception for all Filesystem errors."""
    pass

class PathNotFoundError(FilesystemException):
    """Raised when a path does not exist."""
    pass

class PermissionDeniedError(FilesystemException):
    """Raised when there are no OS permissions to access the path."""
    pass

class ReadOnlyError(FilesystemException):
    """Raised when attempting to modify a read-only path."""
    pass

class DuplicateNameError(FilesystemException):
    """Raised when creating/renaming a file that already exists."""
    pass

class InvalidPathError(FilesystemException):
    """Raised for paths containing invalid characters."""
    pass

class DirectoryTraversalError(FilesystemException):
    """Raised when attempting to access paths outside allowed boundaries."""
    pass

class CircularMoveError(FilesystemException):
    """Raised when attempting to move a folder into itself."""
    pass

class FileLockedError(FilesystemException):
    """Raised when a file is locked by another process."""
    pass

class UnsupportedExtensionError(FilesystemException):
    """Raised when a file extension is not supported for the requested operation."""
    pass
