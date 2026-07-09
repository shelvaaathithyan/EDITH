import threading
from edith.core.interfaces.voice import IVoiceManager
from edith.core.orchestrator import Orchestrator
from edith.core.events import event_bus, AppEvent
from edith.utils.logger import logger

class VoiceSessionController:
    """
    Manages the lifecycle of a voice interaction session.
    Keeps the flow logic out of main.py and handles multi-turn or interruption events in the future.
    """
    def __init__(self, voice_manager: IVoiceManager, orchestrator: Orchestrator):
        self.voice = voice_manager
        self.orchestrator = orchestrator
        self._is_active = False

    def initialize(self):
        """Subscribe to wake events."""
        event_bus.subscribe(AppEvent.WAKE_WORD_DETECTED, self._on_wake_detected)
        
    def _on_wake_detected(self, data=None):
        """
        Triggered by the Wake Engine.
        We run the wake/listen sequence in a background thread so we don't block the EventBus.
        """
        if self._is_active:
            logger.debug("Session already active, ignoring wake word.")
            return
            
        self._is_active = True
        threading.Thread(target=self._run_session, daemon=True, name="VoiceSessionThread").start()

    def _run_session(self):
        try:
            logger.info("Voice Session Started.")
            # wake() plays sound, says "Yes?", and returns transcribed text
            transcription = self.voice.wake()
            
            if transcription and transcription.strip():
                logger.info(f"Session sending transcription to orchestrator: '{transcription}'")
                self.orchestrator.process_input(transcription)
            else:
                logger.info("Session ended: No transcription received.")
                
        except Exception as e:
            logger.error(f"Error during voice session: {e}")
        finally:
            self._is_active = False
