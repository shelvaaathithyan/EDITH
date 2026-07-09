class ContextException(Exception):
    """Base exception for Interaction Context subsystem."""
    pass

class ContextResolutionError(ContextException):
    """Raised when an ambiguous reference cannot be resolved."""
    pass

class AmbiguousContextError(ContextException):
    """Raised when an ambiguous reference matches multiple equally valid contexts."""
    pass

class ExpiredContextError(ContextException):
    """Raised when attempting to access a context that has already expired."""
    pass
