"""
ISpotifyProvider interface for all media backends.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from edith.capabilities.spotify.spotify_models import ProviderHealth, PlaybackState, Track
from edith.capabilities.spotify.spotify_constants import RepeatMode

class ISpotifyProvider(ABC):
    @abstractmethod
    def initialize(self) -> None:
        pass
        
    @abstractmethod
    def health_check(self) -> ProviderHealth:
        pass
        
    @abstractmethod
    def launch(self) -> bool:
        pass
        
    @abstractmethod
    def focus(self) -> bool:
        pass
        
    @abstractmethod
    def play(self) -> bool:
        pass
        
    @abstractmethod
    def pause(self) -> bool:
        pass
        
    @abstractmethod
    def resume(self) -> bool:
        pass
        
    @abstractmethod
    def stop(self) -> bool:
        pass
        
    @abstractmethod
    def next_track(self) -> bool:
        pass
        
    @abstractmethod
    def previous_track(self) -> bool:
        pass
        
    @abstractmethod
    def set_volume(self, percent: int) -> bool:
        pass
        
    @abstractmethod
    def increase_volume(self, percent: int = 10) -> bool:
        pass
        
    @abstractmethod
    def decrease_volume(self, percent: int = 10) -> bool:
        pass
        
    @abstractmethod
    def mute(self) -> bool:
        pass
        
    @abstractmethod
    def unmute(self) -> bool:
        pass
        
    @abstractmethod
    def toggle_shuffle(self) -> bool:
        pass
        
    @abstractmethod
    def set_repeat(self, mode: RepeatMode) -> bool:
        pass
        
    @abstractmethod
    def search_track(self, query: str) -> Optional[Track]:
        pass
        
    @abstractmethod
    def search_album(self, query: str) -> Optional[Track]:
        pass
        
    @abstractmethod
    def search_artist(self, query: str) -> Optional[Track]:
        pass
        
    @abstractmethod
    def search_playlist(self, query: str) -> Optional[Track]:
        pass
        
    @abstractmethod
    def play_track(self, track: Track) -> bool:
        pass
        
    @abstractmethod
    def play_album(self, query: str) -> bool:
        pass
        
    @abstractmethod
    def play_artist(self, query: str) -> bool:
        pass
        
    @abstractmethod
    def play_playlist(self, query: str) -> bool:
        pass
        
    @abstractmethod
    def current_track(self) -> Optional[Track]:
        pass
        
    @abstractmethod
    def like_track(self, track: Track) -> bool:
        pass
        
    @abstractmethod
    def unlike_track(self, track: Track) -> bool:
        pass
        
    @abstractmethod
    def shutdown(self) -> None:
        pass
