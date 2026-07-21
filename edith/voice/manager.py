from typing import Optional, Iterator
from edith.utils.logger import logger
from edith.config.settings import settings
from edith.voice.models import VoiceState, VoiceEvent, VoiceMessage, event_bus
from edith.voice.providers.factory import VoiceProviderFactory

class VoiceManager:
    """
    Public Voice API for EDITH.
    Frozen interface: initialize, listen, listen_stream, speak, interrupt, stop, shutdown, get_state, wake.
    All dependencies injected via constructor — no import-time singletons.
    """
    def __init__(self, stt_provider, scheduler, sound_manager, ptt_controller, audio_player=None):
        self._state = VoiceState.IDLE
        self._stt = stt_provider
        self._scheduler = scheduler
        self._sound_manager = sound_manager
        self._ptt_controller = ptt_controller
        self._audio_player = audio_player

        # Subscribe to scheduler events to update our state
        event_bus.subscribe(VoiceEvent.VOICE_STARTED, self._on_voice_started)
        event_bus.subscribe(VoiceEvent.VOICE_STOPPED, self._on_voice_stopped)

    def _on_voice_started(self, data):
        self._set_state(VoiceState.SPEAKING)

    def _on_voice_stopped(self, data):
        if self._state == VoiceState.SPEAKING:
            self._set_state(VoiceState.IDLE)

    def initialize(self):
        """Initializes TTS providers and starts the speech scheduler."""
        logger.info("Initializing Voice Manager...")
        self._set_state(VoiceState.IDLE)
        tts_provider = VoiceProviderFactory.get_provider(audio_player=self._audio_player)
        self._scheduler.start(tts_provider)
        # Start PTT controller in background
        self._ptt_controller.start()

    def _set_state(self, new_state: VoiceState):
        if self._state != new_state:
            self._state = new_state
            logger.debug(f"VoiceState changed to: {self._state.value}")
            event_bus.publish(VoiceEvent.STATE_CHANGED, self._state)

    def get_state(self) -> VoiceState:
        return self._state

    def wake(self) -> Optional[str]:
        """
        Handles the wake word response sequence.
        Flow: Wake Phrase -> Wake Sound -> "Yes?" -> Listening -> Return text.
        """
        # Play wake sound and respond immediately
        self._sound_manager.play_listening_start()
        
        wake_response = settings.wake_responses[0] if settings.wake_responses else "Yes?"
        
        # High priority so it plays before any other queued speech
        self.speak(wake_response, priority="critical")
        
        import time
        # Wait up to 5 seconds for TTS to finish speaking and release the lock.
        timeout_time = time.time() + 5.0
        time.sleep(0.1) 
        while self.get_state() == VoiceState.SPEAKING:
            if time.time() > timeout_time:
                logger.warning("Wake TTS timeout. Forcing listen.")
                break
            time.sleep(0.1)

        return self.listen()

    def ptt_wake(self) -> Optional[str]:
        """
        Handles the Push-to-Talk sequence.
        Flow: Wake Sound -> Listening (until key release) -> Return text.
        """
        self._sound_manager.play_listening_start()
        return self.listen(ptt_mode=True)

    def listen(self, ptt_mode: bool = False) -> Optional[str]:
        """Listens for user input via microphone."""
        import time
        self._set_state(VoiceState.LISTENING)
        logger.info("🎙 Recording Started")
        event_bus.publish(VoiceEvent.LISTENING_STARTED)
        
        start_time = time.time()
        text = self._stt.listen(ptt_mode=ptt_mode)
        duration = time.time() - start_time
        logger.info(f"🎙 Recording Finished (duration: {duration:.2f}s)")
        
        event_bus.publish(VoiceEvent.LISTENING_FINISHED, text)
        
        if text:
            logger.info(f"Speech recognized: {text}")
        else:
            logger.info("Listening finished, no speech recognized.")
            
        self._set_state(VoiceState.IDLE)
        return text

    def listen_stream(self) -> Iterator[str]:
        """Listens for user input and yields transcriptions incrementally."""
        self._set_state(VoiceState.LISTENING)
        event_bus.publish(VoiceEvent.LISTENING_STARTED)
        
        iterator = self._stt.listen_stream()
        
        for text in iterator:
            if text:
                logger.info(f"Streamed speech recognized: {text}")
            yield text
            
        event_bus.publish(VoiceEvent.LISTENING_FINISHED, None)
        self._set_state(VoiceState.IDLE)

    def speak(self, text: str, priority: str = "normal", interruptible: bool = True):
        """Schedules a message to be spoken via the SpeechScheduler."""
        if not text:
            return

        priority_level = 10
        if priority == "critical":
            priority_level = 1
        elif priority == "high":
            priority_level = 5

        msg = VoiceMessage(text=text, priority=priority, interruptible=interruptible)
        self._scheduler.schedule(msg, priority_level)

    def interrupt(self):
        """Interrupts current speech and clears the queue."""
        logger.info("Voice Manager: User interruption.")
        self._set_state(VoiceState.INTERRUPTED)
        event_bus.publish(VoiceEvent.INTERRUPTED)
        
        self._scheduler.interrupt()

        self._set_state(VoiceState.IDLE)

    def stop(self):
        """Stops current speech gracefully."""
        self._scheduler.stop()

    def shutdown(self):
        """Shuts down the Voice Manager."""
        logger.info("Shutting down Voice Manager...")
        self.stop()

# NO MODULE-LEVEL SINGLETON — created in build_app()
