"""
System Media Provider using Windows SMTC (System Media Transport Controls).
"""

from typing import Optional
from edith.capabilities.spotify.providers.spotify_provider import ISpotifyProvider
from edith.capabilities.spotify.spotify_models import ProviderHealth, Track
from edith.capabilities.spotify.spotify_constants import RepeatMode

class SystemMediaProvider(ISpotifyProvider):
    def __init__(self):
        self._is_initialized = False

    def initialize(self) -> None:
        self._is_initialized = True
        
    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            name="SystemMediaProvider",
            is_initialized=self._is_initialized,
            is_connected=True,
            can_playback=True,
            can_search=False,
            can_control_volume=False,
            latency_ms=5.0,
            details="Mock SMTC provider"
        )
        
    def launch(self) -> bool: return False
    def focus(self) -> bool: return False
    def play(self) -> bool: return True
    def pause(self) -> bool: return True
    def resume(self) -> bool: return True
    def stop(self) -> bool: return True
    def next_track(self) -> bool: return True
    def previous_track(self) -> bool: return True
    def set_volume(self, percent: int) -> bool: return False
    def increase_volume(self, percent: int = 10) -> bool: return False
    def decrease_volume(self, percent: int = 10) -> bool: return False
    def mute(self) -> bool: return False
    def unmute(self) -> bool: return False
    def toggle_shuffle(self) -> bool: return False
    def set_repeat(self, mode: RepeatMode) -> bool: return False
    def search_track(self, query: str) -> Optional[Track]: return None
    def search_album(self, query: str) -> Optional[Track]: return None
    def search_artist(self, query: str) -> Optional[Track]: return None
    def search_playlist(self, query: str) -> Optional[Track]: return None
    def play_track(self, track: Track) -> bool: return False
    def play_album(self, query: str) -> bool: return False
    def play_artist(self, query: str) -> bool: return False
    def play_playlist(self, query: str) -> bool: return False
    def current_track(self) -> Optional[Track]: return None
    def like_track(self, track: Track) -> bool: return False
    def unlike_track(self, track: Track) -> bool: return False
    def shutdown(self) -> None: pass
