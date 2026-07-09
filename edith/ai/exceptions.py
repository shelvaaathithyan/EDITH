class AIException(Exception):
    """Base class for all AI Layer exceptions."""
    pass

class ProviderError(AIException):
    """Raised when the LLM provider fails (e.g., timeout, connection refused)."""
    pass

class JSONValidationError(AIException):
    """Raised when the LLM returns invalid or malformed JSON."""
    pass

class ModelMissingError(AIException):
    """Raised when the specified model is not installed or available."""
    pass
