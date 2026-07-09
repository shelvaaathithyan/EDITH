import queue
import threading
from typing import Optional
from edith.utils.logger import logger
from edith.voice.models import VoiceEvent, VoiceMessage, event_bus
from edith.voice.sounds import sound_manager
from edith.voice.providers.base_provider import BaseTTSProvider

class SpeechScheduler:
    def __init__(self):
        self._queue: queue.PriorityQueue = queue.PriorityQueue()
        self._is_running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._tts_provider: Optional[BaseTTSProvider] = None

    def start(self, tts_provider: BaseTTSProvider):
        """Starts the scheduler worker thread."""
        self._tts_provider = tts_provider
        self._is_running = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        logger.debug("SpeechScheduler started.")

    def schedule(self, msg: VoiceMessage, priority_level: int = 10):
        """Schedules a voice message to be spoken."""
        self._queue.put((priority_level, msg))

    def interrupt(self):
        """Clears the queue and immediately stops any current playback."""
        logger.info("SpeechScheduler: Interruption triggered. Clearing queue...")
        # Clear queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
                
        # Stop current playback
        if self._tts_provider:
            self._tts_provider.interrupt()

    def pause(self):
        """Placeholder for future pause functionality."""
        pass

    def resume(self):
        """Placeholder for future resume functionality."""
        pass

    def _process_queue(self):
        """Worker thread that processes the speech queue."""
        while self._is_running:
            try:
                priority_level, msg = self._queue.get(timeout=0.5)
                
                event_bus.publish(VoiceEvent.VOICE_STARTED, msg)
                
                try:
                    if self._tts_provider:
                        self._tts_provider.speak(msg.text, interruptible=msg.interruptible)
                except Exception as e:
                    logger.error(f"SpeechScheduler: TTS Error during playback: {e}")
                    sound_manager.play_error()
                finally:
                    event_bus.publish(VoiceEvent.VOICE_STOPPED, msg)
                    self._queue.task_done()
                    
            except queue.Empty:
                continue

    def stop(self):
        """Stops the scheduler and shuts down."""
        self._is_running = False
        if self._tts_provider:
            self._tts_provider.stop()
        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)
            
scheduler = SpeechScheduler()
