import os
import tempfile
import time
import speech_recognition as sr
from faster_whisper import WhisperModel
from typing import Optional
from edith.utils.logger import logger
from edith.config.settings import settings
from edith.core.events import event_bus, AppEvent
import numpy as np

class AudioProcessor:
    """Centralized helper for audio validation and conversion."""
    
    @staticmethod
    def to_whisper_numpy(audio_data: sr.AudioData) -> np.ndarray:
        """
        Converts SpeechRecognition AudioData into a Whisper-compatible
        NumPy array (16kHz, mono, float32 normalized to [-1.0, 1.0]).
        """
        raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
        audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
        return audio_np

_whisper_model_instance = None

def get_whisper_model(model_size: str = "base") -> WhisperModel:
    """Initializes WhisperModel with robust automatic CPU/GPU fallback and caching."""
    global _whisper_model_instance
    if _whisper_model_instance is not None:
        return _whisper_model_instance

    try:
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        # Verify CUDA works to catch missing cuBLAS DLLs early
        dummy_audio = np.zeros(16000, dtype=np.float32)
        model.transcribe(dummy_audio)
        logger.info("Whisper backend:\nDevice: CUDA\nCompute: float16")
        _whisper_model_instance = model
        return model
    except Exception as e:
        logger.debug(f"CUDA unavailable or failed ({e}). Falling back to CPU.")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        logger.info("Whisper backend:\nDevice: CPU\nCompute: int8")
        _whisper_model_instance = model
        return model

class STTProvider:
    def __init__(self, microphone_manager=None):
        logger.info("Initializing Whisper STT model...")
        self.model = get_whisper_model("base")
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.processor = AudioProcessor()
        self._microphone = microphone_manager

    def transcribe(self, audio_data: sr.AudioData) -> Optional[str]:
        """Transcribes AudioData into text using the Whisper model directly from memory."""
        try:
            # Diagnostics - Microphone
            duration = len(audio_data.frame_data) / (audio_data.sample_rate * audio_data.sample_width)
            logger.debug(f"[Microphone] sample_rate: {audio_data.sample_rate}Hz, sample_width: {audio_data.sample_width} bytes, duration: {duration:.2f}s")
            
            # Diagnostics - Audio
            event_bus.publish(AppEvent.STT_STARTED)
            start_convert = time.time()
            audio_np = self.processor.to_whisper_numpy(audio_data)
            logger.debug(f"[Audio] normalized: True, resampled: 16000Hz, channels: 1 (mono), prep_time: {time.time() - start_convert:.3f}s")
            
            # Diagnostics - Whisper
            logger.info("📝 Sending audio to Whisper")
            start_infer = time.time()
            segments_generator, info = self.model.transcribe(audio_np, beam_size=5)
            segments = list(segments_generator)
            inference_time = time.time() - start_infer
            
            logger.debug(f"[Whisper] language: {info.language}, confidence: {info.language_probability:.2f}, segments: {len(segments)}, inference_time: {inference_time:.3f}s")
            
            if len(segments) == 0:
                logger.warning(f"[Whisper] Zero segments returned. Duration: {duration:.2f}s. Audio may be empty or pure noise.")
                return None
            
            text = "".join([segment.text for segment in segments]).strip()
            logger.info(f"📝 Whisper Response: {text}")
            
            # Filter out common whisper hallucinations for silence
            hallucinations = ["Thanks for watching!", "Subtitles by Amara.org", "Thank you.", ""]
            if text in hallucinations or len(text) < 2:
                logger.debug(f"[Whisper] Hallucination filtered: '{text}'")
                event_bus.publish(AppEvent.STT_FINISHED, None)
                return None
                
            event_bus.publish(AppEvent.STT_FINISHED, text)
            return text

        except Exception as e:
            logger.error(f"STT Transcription Error: {e}")
            event_bus.publish(AppEvent.STT_FINISHED, None)
            return None

    def capture_audio(self, ptt_mode: bool = False) -> Optional[sr.AudioData]:
        """Captures audio from the microphone and returns AudioData."""
        if self._microphone and self._microphone.is_locked:
            logger.debug("Microphone is currently locked (EDITH is likely speaking).")
            return None

        # Use the configured microphone index if set
        device_index = settings.microphone_index
        try:
            with sr.Microphone(device_index=device_index) as source:
                if settings.ambient_noise_calibration:
                    logger.debug("Calibrating for ambient noise...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Check lock again right before listening just to be safe
                if self._microphone and self._microphone.is_locked:
                    return None
                    
                import time
                start_time = time.time()
                logger.info("🎙 Recording Started")
                
                if ptt_mode:
                    import keyboard
                    logger.info("🎙 PTT Mode: Recording strictly until '7' is released...")
                    frames = []
                    # Clear existing frames from stream buffer
                    source.stream.read(source.CHUNK)
                    while keyboard.is_pressed('7'):
                        buffer = source.stream.read(source.CHUNK)
                        frames.append(buffer)
                    audio_data = sr.AudioData(b"".join(frames), source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                else:
                    try:
                        audio_data = self.recognizer.listen(
                            source, 
                            timeout=settings.silence_timeout, 
                            phrase_time_limit=settings.record_timeout
                        )
                    except sr.WaitTimeoutError:
                        return None
                        
                duration = time.time() - start_time
                bytes_captured = len(audio_data.frame_data)
                logger.info("🎙 Recording Finished")
                logger.info(f"   Duration: {duration:.2f}s")
                logger.info(f"   Bytes Captured: {bytes_captured}")
                logger.info(f"   Sample Rate: {audio_data.sample_rate}Hz")
                logger.info(f"   Channels: 1 (Mono)")
                
                return audio_data

        except OSError as e:
            logger.error(f"Microphone access error: {e}")
            return None
        except Exception as e:
            logger.error(f"STT Error: {e}")
            return None

    def listen(self, ptt_mode: bool = False) -> Optional[str]:
        """Captures audio and immediately transcribes it."""
        audio_data = self.capture_audio(ptt_mode=ptt_mode)
        if audio_data:
            return self.transcribe(audio_data)
        return None

    def listen_stream(self):
        """
        Placeholder for future streaming transcription.
        Currently yields the final transcription once to satisfy the Iterator contract.
        """
        from typing import Iterator
        def _generator() -> Iterator[str]:
            text = self.listen()
            if text:
                yield text
        return _generator()

# NO MODULE-LEVEL SINGLETON — created in build_app()
