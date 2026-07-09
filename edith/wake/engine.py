import threading
import time
import numpy as np
import pyaudio
from edith.utils.logger import logger
from edith.core.events import event_bus, AppEvent
from edith.ai.models import HealthStatus

class WakeEngine:
    def __init__(self, model_paths=None, chunk_size=1280, sensitivity=0.5):
        """
        Initializes the Wake Engine.
        In a true production environment, `model_paths` would point to a custom 
        'Hello EDITH' .onnx model. We'll use a default or handle missing models gracefully.
        """
        self.chunk_size = chunk_size
        self.sensitivity = sensitivity
        self.is_running = False
        self._thread = None
        self._audio = None
        self._stream = None
        
        try:
            from openwakeword.model import Model
            # We use a default model if a custom 'hello_edith' isn't provided
            # e.g., "hey_jarvis" as a placeholder if needed
            self.model = Model(wakeword_models=model_paths or ["hey_jarvis"], inference_framework="onnx")
            self._healthy = True
        except Exception as e:
            logger.error(f"Failed to load OpenWakeWord model: {e}")
            self._healthy = False
            self.model = None

    def initialize(self):
        """Lifecycle initialization"""
        self.start()

    def health_check(self) -> HealthStatus:
        if self._healthy:
            return HealthStatus(status="healthy")
        return HealthStatus(status="unhealthy", error="Failed to load wake word model")

    def start(self):
        if self.is_running or not self._healthy:
            return
            
        self.is_running = True
        self._audio = pyaudio.PyAudio()
        
        try:
            self._stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self._thread = threading.Thread(target=self._listen_loop, daemon=True, name="WakeEngineThread")
            self._thread.start()
            logger.info("Wake Engine started listening in the background.")
        except Exception as e:
            logger.error(f"Failed to start audio stream for Wake Engine: {e}")
            self.is_running = False

    def stop(self):
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            
        if self._audio:
            self._audio.terminate()
            
        logger.info("Wake Engine stopped.")

    def shutdown(self):
        """Lifecycle shutdown"""
        self.stop()

    def _listen_loop(self):
        logger.debug("Wake engine loop active.")
        while self.is_running:
            try:
                # Read audio chunk
                data = self._stream.read(self.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # Predict
                prediction = self.model.predict(audio_data)
                
                # Check thresholds
                for mdl, score in prediction.items():
                    if score > self.sensitivity:
                        logger.info(f"Wake word detected! ({mdl}: {score})")
                        
                        # Fire global event
                        event_bus.publish(AppEvent.WAKE_WORD_DETECTED)
                        
                        # Sleep briefly to prevent multiple triggers for the same utterance
                        time.sleep(2.0)
                        
                        # Clear buffer to prevent stale audio from triggering again
                        # (In openwakeword, typically we reset internal state if available, or just skip)
                        # OpenWakeWord state is maintained internally.
                        
            except Exception as e:
                logger.error(f"Error in Wake Engine loop: {e}")
                time.sleep(1) # Prevent tight error loops
