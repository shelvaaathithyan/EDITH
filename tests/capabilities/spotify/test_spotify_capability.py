import pytest
from unittest.mock import MagicMock
from edith.capabilities.spotify.providers.provider_manager import SpotifyProviderManager
from edith.capabilities.spotify.spotify_controller import SpotifyController
from edith.capabilities.spotify.spotify_models import Track, ProviderHealth
from edith.capabilities.spotify.spotify_constants import SpotifyState

def test_provider_manager_selection():
    manager = SpotifyProviderManager()
    
    # Mocking Desktop Provider as Healthy
    manager.providers[1].health_check = MagicMock(return_value=ProviderHealth(
        name="MockDesktop", is_initialized=True, is_connected=True, can_search=True
    ))
    
    # Mocking Web API as Unhealthy
    manager.providers[0].health_check = MagicMock(return_value=ProviderHealth(
        name="MockWeb", is_initialized=True, is_connected=False
    ))
    
    best = manager.get_best_provider(require_search=True)
    assert best.__class__.__name__ == "DesktopSpotifyProvider"

def test_controller_play_flow():
    controller = SpotifyController()
    
    # Force Mock Provider
    mock_provider = MagicMock()
    mock_provider.health_check.return_value = ProviderHealth(
        name="MockProvider", is_initialized=True, is_connected=True, can_search=True
    )
    mock_provider.play_track.return_value = True
    
    controller.provider_manager.providers = [mock_provider]
    controller.initialize()
    
    assert controller.state == SpotifyState.READY
    
    success = controller.play_track("Believer")
    
    assert success is True
    assert controller.state == SpotifyState.PLAYING
    assert controller.cache.current_track.title == "Believer"
    
def test_controller_pause_flow():
    controller = SpotifyController()
    mock_provider = MagicMock()
    mock_provider.health_check.return_value = ProviderHealth(
        name="MockProvider", is_initialized=True, is_connected=True
    )
    mock_provider.pause.return_value = True
    controller.provider_manager.providers = [mock_provider]
    
    success = controller.pause()
    assert success is True
    assert controller.state == SpotifyState.PAUSED
