"""
Spotify Provider Manager.
Dynamically resolves the best provider for an action.
"""

from typing import List, Optional
from edith.capabilities.spotify.providers.spotify_provider import ISpotifyProvider
from edith.capabilities.spotify.providers.desktop_spotify_provider import DesktopSpotifyProvider
from edith.capabilities.spotify.providers.system_media_provider import SystemMediaProvider
from edith.capabilities.spotify.providers.web_api_spotify_provider import WebApiSpotifyProvider
from edith.capabilities.spotify.spotify_exceptions import ProviderUnavailableError
from edith.utils.logger import logger

class SpotifyProviderManager:
    def __init__(self):
        self.providers: List[ISpotifyProvider] = [
            WebApiSpotifyProvider(),
            DesktopSpotifyProvider(),
            SystemMediaProvider()
        ]
        
    def initialize_all(self):
        for provider in self.providers:
            try:
                provider.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider.__class__.__name__}: {e}")

    def get_best_provider(self, require_search: bool = False, require_volume: bool = False) -> ISpotifyProvider:
        """
        Dynamically selects a provider based on health and capabilities.
        """
        for provider in self.providers:
            health = provider.health_check()
            if not health.is_initialized or not health.is_connected:
                continue
                
            if require_search and not health.can_search:
                continue
                
            if require_volume and not health.can_control_volume:
                continue
                
            return provider
            
        # Fallback to the first initialized one if we just need basic playback
        for provider in self.providers:
            if provider.health_check().is_initialized:
                return provider
                
        raise ProviderUnavailableError("No suitable Spotify provider is available.")
