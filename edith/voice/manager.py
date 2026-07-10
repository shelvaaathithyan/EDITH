from typing import Optional, Iterator
from edith.utils.logger import logger
from edith.config.settings import settings
from edith.voice.models import VoiceState, VoiceEvent, VoiceMessage, event_bus
from edith.voice.sounds import sound_manager
from edith.voice.stt import stt
from edith.voice.scheduler import scheduler
from edith.voice.providers.factory import VoiceProviderFactory
from edith.voice.ptt import ptt_controller

class VoiceManager:
    """
    Public Voice API for EDITH.
    Frozen interface: initialize, listen, listen_stream, speak, interrupt, stop, shutdown, get_state, wake.
    """
    def __init__(self):
        self._state = VoiceState.IDLE
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
        tts_provider = VoiceProviderFactory.get_provider()
        scheduler.start(tts_provider)
        # Start PTT controller in background
        ptt_controller.start()

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
        sound_manager.play_listening_start()
        
        wake_response = settings.wake_responses[0] if settings.wake_responses else "Yes?"
        
        # High priority so it plays before any other queued speech
        # It blocks because the scheduler processes it, but wait, speak() queues it.
        # To make sure we don't start listening while speaking, we rely on the microphone lock.
        # But wait, we want to play the wake sound, say "Yes?", then start listening.
        self.speak(wake_response, priority="critical")
        
        # The microphone lock will prevent listen() from recording until the speech finishes.
        # However, `speak()` is asynchronous via the queue. So `stt.listen()` might run and return None 
        # because the mic is locked.
        # So we need to either wait for speech to finish, or just call listen() which will block until it gets audio.
        # Wait, if stt.listen() is called while mic is locked, it currently immediately returns None.
        # We need to wait for the speaking to finish if we want to listen *after*.
        # The simplest way is to listen
        # which respects the lock by returning None, wait, we don't want it to return None.
        # We can poll the lock or `VoiceState` before calling listen().
        import time
        # Wait up to 5 seconds for TTS to finish speaking and release the lock.
        # This prevents the race condition where `listen` executes while `microphone` is still locked.
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
        sound_manager.play_listening_start()
        return self.listen(ptt_mode=True)

    def listen(self, ptt_mode: bool = False) -> Optional[str]:
        """Listens for user input via microphone."""
        import time
        self._set_state(VoiceState.LISTENING)
        logger.info("🎙 Recording Started")
        event_bus.publish(VoiceEvent.LISTENING_STARTED)
        
        start_time = time.time()
        text = stt.listen(ptt_mode=ptt_mode)
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
        
        iterator = stt.listen_stream()
        
        for text in iterator:
            if text:
                logger.info(f"Streamed speech recognized: {text}")
            yield text
            
        event_bus.publish(VoiceEvent.LISTENING_FINISHED, None) # Or pass final text
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
        scheduler.schedule(msg, priority_level)

    def interrupt(self):
        """Interrupts current speech and clears the queue."""
        logger.info("Voice Manager: User interruption.")
        self._set_state(VoiceState.INTERRUPTED)
        event_bus.publish(VoiceEvent.INTERRUPTED)
        
        scheduler.interrupt()

        self._set_state(VoiceState.IDLE)

    def stop(self):
        """Stops current speech gracefully."""
        scheduler.stop()

    def shutdown(self):
        """Shuts down the Voice Manager."""
        logger.info("Shutting down Voice Manager...")
        self.stop()

# Export singleton
voice_manager = VoiceManager()
