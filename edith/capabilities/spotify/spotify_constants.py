"""
Constants for the Spotify Capability.
"""

from enum import Enum

class SpotifyAction(str, Enum):
    PLAY_TRACK = "play_track"
    PLAY_ALBUM = "play_album"
    PLAY_ARTIST = "play_artist"
    PLAY_PLAYLIST = "play_playlist"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    NEXT_TRACK = "next_track"
    PREVIOUS_TRACK = "previous_track"
    SET_VOLUME = "set_volume"
    INCREASE_VOLUME = "increase_volume"
    DECREASE_VOLUME = "decrease_volume"
    MUTE = "mute"
    UNMUTE = "unmute"
    TOGGLE_SHUFFLE = "toggle_shuffle"
    SET_REPEAT = "set_repeat"
    LIKE_TRACK = "like_track"
    UNLIKE_TRACK = "unlike_track"
    CURRENT_TRACK = "current_track"
    OPEN = "open"

class SpotifyState(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    STARTING = "STARTING"
    READY = "READY"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    SEARCHING = "SEARCHING"
    ERROR = "ERROR"

class RepeatMode(str, Enum):
    OFF = "off"
    TRACK = "track"
    CONTEXT = "context"
