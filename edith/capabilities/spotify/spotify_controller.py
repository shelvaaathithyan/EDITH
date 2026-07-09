"""
Spotify Controller. The orchestrator of the capability.
"""

from edith.capabilities.spotify.providers.provider_manager import SpotifyProviderManager
from edith.capabilities.spotify.spotify_context import SearchResolver
from edith.capabilities.spotify.spotify_utils import MetadataCache
from edith.capabilities.spotify.spotify_models import Track
from edith.capabilities.spotify.spotify_constants import SpotifyState
from edith.capabilities.spotify.spotify_exceptions import SpotifyException, ProviderUnavailableError
from edith.core.events import event_bus, AppEvent
from edith.utils.logger import logger
from typing import Optional

class SpotifyController:
    def __init__(self):
        self.provider_manager = SpotifyProviderManager()
        self.search_resolver = SearchResolver()
        self.cache = MetadataCache()
        self.state = SpotifyState.DISCONNECTED

    def initialize(self):
        self.state = SpotifyState.STARTING
        self.provider_manager.initialize_all()
        self.state = SpotifyState.READY

    def play_track(self, query: str) -> bool:
        try:
            provider = self.provider_manager.get_best_provider(require_search=True)
            track = self.search_resolver.resolve_track(query)
            
            success = provider.play_track(track)
            if success:
                self.state = SpotifyState.PLAYING
                self.cache.update_track(track)
                event_bus.publish(AppEvent.PLAYBACK_STARTED, {"track": track.model_dump()})
                
            return success
        except ProviderUnavailableError:
            self.state = SpotifyState.ERROR
            raise SpotifyException("Cannot play track. No provider available.")
            
    def pause(self) -> bool:
        provider = self.provider_manager.get_best_provider()
        success = provider.pause()
        if success:
            self.state = SpotifyState.PAUSED
            event_bus.publish(AppEvent.PLAYBACK_PAUSED, {})
        return success
        
    def get_current_state(self) -> SpotifyState:
        return self.state
