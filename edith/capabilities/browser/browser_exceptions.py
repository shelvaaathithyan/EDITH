class BrowserException(Exception):
    """Base exception for Browser Capability errors."""
    pass

class BrowserNotFoundError(BrowserException):
    """Raised when the requested browser is not installed."""
    pass

class BrowserLaunchError(BrowserException):
    """Raised when a browser process fails to start."""
    pass

class InvalidBrowserActionError(BrowserException):
    """Raised when the Planner requests an unsupported browser action."""
    pass
