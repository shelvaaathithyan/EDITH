"""
Metadata Cache for the Spotify Capability.
"""

from typing import Optional
from edith.capabilities.spotify.spotify_models import Track, PlaybackQueue

class MetadataCache:
    def __init__(self):
        self.current_track: Optional[Track] = None
        self.queue = PlaybackQueue()
        self.playback_position: int = 0
        self.duration_ms: int = 0
        
    def update_track(self, track: Track):
        if self.current_track:
            self.queue.previous.append(self.current_track)
        self.current_track = track
        self.duration_ms = track.duration_ms or 0
        self.playback_position = 0
        
    def update_position(self, position_ms: int):
        self.playback_position = position_ms
