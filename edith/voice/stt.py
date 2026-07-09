import os
import tempfile
import speech_recognition as sr
from faster_whisper import WhisperModel
from typing import Optional
from edith.utils.logger import logger
from edith.config.settings import settings
from edith.voice.microphone import microphone

class STTProvider:
    def __init__(self):
        logger.info("Initializing Whisper STT model...")
        self.model = WhisperModel("base", device="cpu", compute_type="int8")
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True

    def listen(self) -> Optional[str]:
        """Listens to the microphone and returns the transcribed text."""
        if microphone.is_locked:
            logger.debug("Microphone is currently locked (EDITH is likely speaking).")
            return None

        # Use the configured microphone index if set
        device_index = settings.microphone_index
        try:
            with sr.Microphone(device_index=device_index) as source:
                if settings.ambient_noise_calibration:
                    logger.debug("Calibrating for ambient noise...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                try:
                    # Check lock again right before listening just to be safe
                    if microphone.is_locked:
                        return None
                        
                    audio_data = self.recognizer.listen(
                        source, 
                        timeout=settings.silence_timeout, 
                        phrase_time_limit=settings.record_timeout
                    )
                    
                    # Save to temp file for faster-whisper
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                        temp_wav.write(audio_data.get_wav_data())
                        temp_path = temp_wav.name

                    segments, info = self.model.transcribe(temp_path, beam_size=5)
                    text = "".join([segment.text for segment in segments]).strip()
                    os.remove(temp_path)
                    
                    # Filter out common whisper hallucinations for silence
                    hallucinations = ["Thanks for watching!", "Subtitles by Amara.org", "Thank you.", ""]
                    if text in hallucinations or len(text) < 2:
                        return None
                        
                    return text

                except sr.WaitTimeoutError:
                    return None
        except OSError as e:
            logger.error(f"Microphone access error: {e}")
            return None
        except Exception as e:
            logger.error(f"STT Error: {e}")
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

stt = STTProvider()
