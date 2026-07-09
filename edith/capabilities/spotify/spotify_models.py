"""
Models for the Spotify Capability.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class Track(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None
    duration_ms: Optional[int] = 0
    artwork_url: Optional[str] = None
    uri: Optional[str] = None

class PlaybackState(BaseModel):
    is_playing: bool = False
    current_track: Optional[Track] = None
    position_ms: int = 0
    volume_percent: int = 50
    shuffle_state: bool = False
    repeat_state: str = "off"

class PlaybackQueue(BaseModel):
    current: Optional[Track] = None
    previous: List[Track] = Field(default_factory=list)
    upcoming: List[Track] = Field(default_factory=list)

class ProviderHealth(BaseModel):
    name: str
    is_initialized: bool = False
    is_connected: bool = False
    can_playback: bool = False
    can_search: bool = False
    can_control_volume: bool = False
    latency_ms: float = 0.0
    details: str = ""
