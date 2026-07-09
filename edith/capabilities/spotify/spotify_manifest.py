"""
Manifest definition for the Spotify Capability.
"""

from edith.sdk.capability.capability_models import CapabilityManifest
from edith.permission.permission_models import RiskLevel
from edith.capabilities.spotify.spotify_constants import SpotifyAction

def get_spotify_manifest() -> CapabilityManifest:
    actions = [action for action in SpotifyAction]
    
    # All Spotify actions default to LOW Risk. No confirmation required.
    risk_matrix = {action: RiskLevel.LOW for action in SpotifyAction}

    return CapabilityManifest(
        id="core.spotify",
        name="Spotify Media Controller",
        version="1.0.0",
        author="EDITH Core",
        description="Grants EDITH the ability to control media playback securely across multiple providers.",
        supported_platforms=["windows", "macos", "linux"],
        dependencies=[], 
        supported_actions=actions,
        risk_matrix=risk_matrix
    )
