import threading
from typing import Optional
from edith.utils.logger import logger
from edith.config.settings import settings
from edith.voice.models import event_bus, VoiceEvent

class MicrophoneManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._is_locked = False
        
        # Subscribe to voice events to auto-lock the microphone
        event_bus.subscribe(VoiceEvent.VOICE_STARTED, self._on_voice_started)
        event_bus.subscribe(VoiceEvent.VOICE_STOPPED, self._on_voice_stopped)

    def _on_voice_started(self, data):
        self.lock()

    def _on_voice_stopped(self, data):
        self.unlock()

    def lock(self):
        """Locks the microphone (prevents listening)."""
        with self._lock:
            if not self._is_locked:
                self._is_locked = True
                logger.debug("Microphone locked.")

    def unlock(self):
        """Unlocks the microphone (allows listening)."""
        with self._lock:
            if self._is_locked:
                self._is_locked = False
                logger.debug("Microphone unlocked.")

    @property
    def is_locked(self) -> bool:
        with self._lock:
            return self._is_locked

microphone = MicrophoneManager()
