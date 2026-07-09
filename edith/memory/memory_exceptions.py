"""
Exceptions for the Long-Term Memory Subsystem.
"""

class MemoryException(Exception):
    """Base exception for all memory-related errors."""
    pass

class MemoryNotFoundError(MemoryException):
    """Raised when a specific memory ID is not found."""
    pass

class ProviderNotAvailableError(MemoryException):
    """Raised when an active memory provider (like Sqlite or Embedding) fails."""
    pass

class MemoryValidationError(MemoryException):
    """Raised when attempting to store an invalid memory object."""
    pass
