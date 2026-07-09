class PermissionException(Exception):
    """Base exception for the Permission Manager subsystem."""
    pass

class PermissionDeniedError(PermissionException):
    """Raised when an action is denied by the policy or user."""
    pass

class PendingActionExpiredError(PermissionException):
    """Raised when attempting to confirm an action that has expired."""
    pass

class PendingActionNotFoundError(PermissionException):
    """Raised when a referenced pending action does not exist."""
    pass
