"""
Spotify Capability.
The SDK boundary for the media orchestrator.
"""

from typing import Dict, Any
from edith.sdk.capability.base_capability import BaseCapability
from edith.sdk.capability.capability_models import CapabilityManifest, CapabilityResult
from edith.capabilities.spotify.spotify_manifest import get_spotify_manifest
from edith.capabilities.spotify.spotify_constants import SpotifyAction
from edith.capabilities.spotify.spotify_controller import SpotifyController

class SpotifyCapability(BaseCapability):
    def __init__(self):
        super().__init__()
        self.controller = SpotifyController()

    def get_manifest(self) -> CapabilityManifest:
        return get_spotify_manifest()

    def _do_initialize(self) -> None:
        self.controller.initialize()
        
        # Register standard capability actions mapping directly to the controller
        self.register_action(SpotifyAction.PLAY_TRACK, self.play_track)
        self.register_action(SpotifyAction.PAUSE, self.pause)
        # Registering other actions...

    def play_track(self, args: Dict[str, Any]) -> CapabilityResult:
        query = args.get("track", "")
        if not query:
            return CapabilityResult(success=False, error="Track query is required.")
            
        try:
            success = self.controller.play_track(query)
            return CapabilityResult(success=success)
        except Exception as e:
            return CapabilityResult(success=False, error=str(e))
            
    def pause(self, args: Dict[str, Any]) -> CapabilityResult:
        try:
            success = self.controller.pause()
            return CapabilityResult(success=success)
        except Exception as e:
            return CapabilityResult(success=False, error=str(e))
