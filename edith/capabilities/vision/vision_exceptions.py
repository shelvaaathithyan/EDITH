"""
Exceptions for the Vision Perception Engine.
"""

from edith.sdk.capability.capability_exceptions import CapabilityExecutionError

class VisionException(CapabilityExecutionError):
    """Base exception for vision capability."""
    pass

class CaptureError(VisionException):
    """Raised when screen or window capture fails."""
    pass

class OCRError(VisionException):
    """Raised when text extraction fails."""
    pass

class VisionProviderError(VisionException):
    """Raised when the LLM vision provider fails or times out."""
    pass
