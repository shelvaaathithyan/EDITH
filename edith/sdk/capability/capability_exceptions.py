class CapabilityException(Exception):
    """Base exception for all Capability SDK errors."""
    pass

class CapabilityInitializationError(CapabilityException):
    """Raised when a capability fails to initialize."""
    pass

class CapabilityExecutionError(CapabilityException):
    """Raised when an error occurs during execution."""
    pass

class CapabilityValidationError(CapabilityException):
    """Raised when action parameters or paths fail validation."""
    pass

class CapabilityUnavailableError(CapabilityException):
    """Raised when a capability is requested but its health is unhealthy/unavailable."""
    pass

class CapabilityActionNotFoundError(CapabilityException):
    """Raised when a capability does not support the requested action."""
    pass
