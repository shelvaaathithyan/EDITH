"""
Exceptions for the Spotify Capability.
"""

from edith.sdk.capability.capability_exceptions import CapabilityExecutionError

class SpotifyException(CapabilityExecutionError):
    """Base exception for Spotify capability."""
    pass

class ProviderUnavailableError(SpotifyException):
    """Raised when no suitable provider can handle the request."""
    pass

class PlaybackError(SpotifyException):
    """Raised when playback fails to start, pause, or skip."""
    pass

class SearchError(SpotifyException):
    """Raised when a track/album/artist/playlist search fails."""
    pass
