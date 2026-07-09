"""
Desktop Spotify Provider.
Controls the local Spotify application via process management,
window focus, and keyboard simulation.
"""

import subprocess
import time
import shutil
from typing import Optional
from edith.capabilities.spotify.providers.spotify_provider import ISpotifyProvider
from edith.capabilities.spotify.spotify_models import ProviderHealth, Track
from edith.capabilities.spotify.spotify_constants import RepeatMode
from edith.utils.logger import get_logger

logger = get_logger("edith.capabilities.spotify.desktop")

# Keyboard simulation keys (Windows virtual key codes via pyautogui)
_SPOTIFY_PROCESS = "Spotify.exe"


class DesktopSpotifyProvider(ISpotifyProvider):
    """
    Controls Spotify via the local desktop application.
    Uses subprocess for launching, pygetwindow for focus,
    and pyautogui for keyboard media controls.
    """

    def __init__(self):
        self._is_initialized = False
        self._is_connected = False
        self._volume = 50

    def initialize(self) -> None:
        self._is_initialized = True
        self._is_connected = self._is_spotify_running()
        logger.info(f"DesktopSpotifyProvider initialized. Connected={self._is_connected}")

    def health_check(self) -> ProviderHealth:
        installed = shutil.which("spotify") is not None or self._find_spotify_path() is not None
        running = self._is_spotify_running()
        self._is_connected = running

        return ProviderHealth(
            name="DesktopSpotifyProvider",
            is_initialized=self._is_initialized,
            is_connected=running,
            can_playback=running,
            can_search=False,  # Desktop app does not expose a search API
            can_control_volume=True,
            latency_ms=5.0,
            details=f"Installed={installed}, Running={running}"
        )

    # ── Lifecycle ────────────────────────────────────────────

    def launch(self) -> bool:
        if self._is_spotify_running():
            logger.info("Spotify is already running.")
            return True

        path = self._find_spotify_path()
        if not path:
            logger.error("Spotify executable not found on this system.")
            return False

        try:
            subprocess.Popen([path], shell=False)
            logger.info("Launched Spotify. Waiting for startup...")
            # Wait for Spotify to become responsive
            for _ in range(15):
                time.sleep(1)
                if self._is_spotify_running():
                    self._is_connected = True
                    logger.info("Spotify is now running.")
                    return True
            logger.warning("Spotify launched but did not become responsive in time.")
            return False
        except Exception as e:
            logger.error(f"Failed to launch Spotify: {e}")
            return False

    def focus(self) -> bool:
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle("Spotify")
            if windows:
                win = windows[0]
                if win.isMinimized:
                    win.restore()
                win.activate()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to focus Spotify window: {e}")
            return False

    def shutdown(self) -> None:
        self._is_connected = False

    # ── Playback Controls ────────────────────────────────────

    def play(self) -> bool:
        return self._send_media_key("play_pause")

    def pause(self) -> bool:
        return self._send_media_key("play_pause")

    def resume(self) -> bool:
        return self._send_media_key("play_pause")

    def stop(self) -> bool:
        return self._send_media_key("stop")

    def next_track(self) -> bool:
        return self._send_media_key("next_track")

    def previous_track(self) -> bool:
        return self._send_media_key("prev_track")

    # ── Volume ────────────────────────────────────────────────

    def set_volume(self, percent: int) -> bool:
        try:
            import pyautogui
            # Focus Spotify first, then use Ctrl+Up/Down to adjust
            self.focus()
            time.sleep(0.2)

            # Rough adjustment: Spotify uses Ctrl+Up/Ctrl+Down for ~10% increments
            diff = percent - self._volume
            steps = abs(diff) // 10
            key = "up" if diff > 0 else "down"

            for _ in range(steps):
                pyautogui.hotkey("ctrl", key)
                time.sleep(0.05)

            self._volume = max(0, min(100, percent))
            return True
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False

    def increase_volume(self, percent: int = 10) -> bool:
        return self.set_volume(self._volume + percent)

    def decrease_volume(self, percent: int = 10) -> bool:
        return self.set_volume(self._volume - percent)

    def mute(self) -> bool:
        return self.set_volume(0)

    def unmute(self) -> bool:
        return self.set_volume(50)

    # ── Shuffle / Repeat ──────────────────────────────────────

    def toggle_shuffle(self) -> bool:
        try:
            import pyautogui
            self.focus()
            time.sleep(0.2)
            pyautogui.hotkey("ctrl", "s")
            return True
        except Exception as e:
            logger.error(f"Failed to toggle shuffle: {e}")
            return False

    def set_repeat(self, mode: RepeatMode) -> bool:
        try:
            import pyautogui
            self.focus()
            time.sleep(0.2)
            pyautogui.hotkey("ctrl", "r")
            return True
        except Exception as e:
            logger.error(f"Failed to set repeat: {e}")
            return False

    # ── Search (limited in desktop mode) ──────────────────────

    def search_track(self, query: str) -> Optional[Track]:
        """Opens Spotify search via Ctrl+L and types the query."""
        try:
            import pyautogui
            if not self._is_spotify_running():
                self.launch()

            self.focus()
            time.sleep(0.3)

            # Ctrl+L focuses the search bar in Spotify desktop
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.3)
            pyautogui.typewrite(query, interval=0.03)
            time.sleep(0.5)
            # Press Enter to search, then Enter again to play first result
            pyautogui.press("enter")
            time.sleep(1.0)
            pyautogui.press("enter")

            return Track(title=query, artist="Unknown")
        except Exception as e:
            logger.error(f"Desktop search failed: {e}")
            return None

    def search_album(self, query: str) -> Optional[Track]:
        return self.search_track(query)

    def search_artist(self, query: str) -> Optional[Track]:
        return self.search_track(query)

    def search_playlist(self, query: str) -> Optional[Track]:
        return self.search_track(query)

    # ── Playback Actions ──────────────────────────────────────

    def play_track(self, track: Track) -> bool:
        result = self.search_track(track.title)
        return result is not None

    def play_album(self, query: str) -> bool:
        result = self.search_track(query)
        return result is not None

    def play_artist(self, query: str) -> bool:
        result = self.search_track(query)
        return result is not None

    def play_playlist(self, query: str) -> bool:
        result = self.search_track(query)
        return result is not None

    # ── Metadata ──────────────────────────────────────────────

    def current_track(self) -> Optional[Track]:
        """Attempts to read the current track from the Spotify window title."""
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle("Spotify")
            for win in windows:
                title = win.title
                if " - " in title and title != "Spotify" and title != "Spotify Premium":
                    parts = title.split(" - ", 1)
                    return Track(title=parts[1].strip() if len(parts) > 1 else title, artist=parts[0].strip())
            return None
        except Exception:
            return None

    def like_track(self, track: Track) -> bool:
        try:
            import pyautogui
            self.focus()
            time.sleep(0.2)
            pyautogui.hotkey("alt", "shift", "b")  # Spotify like shortcut
            return True
        except Exception:
            return False

    def unlike_track(self, track: Track) -> bool:
        return self.like_track(track)  # Same toggle

    # ── Private Helpers ───────────────────────────────────────

    def _is_spotify_running(self) -> bool:
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {_SPOTIFY_PROCESS}"],
                capture_output=True, text=True, timeout=5
            )
            return _SPOTIFY_PROCESS.lower() in result.stdout.lower()
        except Exception:
            return False

    def _find_spotify_path(self) -> Optional[str]:
        """Finds the Spotify executable on the system."""
        import os
        common_paths = [
            os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\Spotify.exe"),
            r"C:\Program Files\Spotify\Spotify.exe",
            r"C:\Program Files (x86)\Spotify\Spotify.exe",
        ]
        for path in common_paths:
            if os.path.isfile(path):
                return path

        # Fallback: try shutil.which
        found = shutil.which("spotify")
        return found

    def _send_media_key(self, key_name: str) -> bool:
        """Sends a system-wide media key press."""
        try:
            import pyautogui
            key_map = {
                "play_pause": "playpause",
                "next_track": "nexttrack",
                "prev_track": "prevtrack",
                "stop": "stop",
                "volume_up": "volumeup",
                "volume_down": "volumedown",
                "volume_mute": "volumemute",
            }
            key = key_map.get(key_name)
            if key:
                pyautogui.press(key)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to send media key '{key_name}': {e}")
            return False
