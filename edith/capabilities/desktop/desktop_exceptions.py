class DesktopException(Exception):
    """Base exception for Desktop Capability errors."""
    pass

class ApplicationNotFoundError(DesktopException):
    """Raised when an application executable cannot be found in the system."""
    pass

class ApplicationLaunchError(DesktopException):
    """Raised when a desktop application fails to start."""
    pass

class InvalidDesktopActionError(DesktopException):
    """Raised when the Planner requests an unsupported action."""
    pass

class WindowFocusError(DesktopException):
    """Raised when the application is running but the window cannot be focused."""
    pass
