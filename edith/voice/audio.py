import sounddevice as sd
import soundfile as sf
import threading
import numpy as np
from typing import Optional
from edith.utils.logger import logger
from edith.config.settings import settings

class AudioPlayer:
    def __init__(self):
        self._current_stream: Optional[sd.OutputStream] = None
        self._lock = threading.Lock()

    def play_wav(self, file_path: str, block: bool = True):
        """Plays a WAV file. If block=True, waits until playback is finished."""
        try:
            data, fs = sf.read(file_path)
            # Apply volume setting
            if settings.volume != 1.0:
                data = data * settings.volume

            # Ensure data is float32 to prevent sounddevice dtype mismatch exceptions
            data = np.asarray(data, dtype=np.float32)

            logger.debug(f"[AudioPlayer] Playing: {file_path} | shape={data.shape} | dtype={data.dtype} | samplerate={fs}")

            with self._lock:
                self._current_stream = sd.OutputStream(
                    samplerate=fs, 
                    channels=data.ndim if len(data.shape) > 1 else 1,
                    dtype=np.float32
                )
                self._current_stream.start()

            # Play the audio
            self._current_stream.write(data)

            with self._lock:
                if self._current_stream:
                    self._current_stream.stop()
                    self._current_stream.close()
                    self._current_stream = None

        except sd.PortAudioError as e:
            if "Stream is stopped" in str(e):
                # This is fine, we interrupted it
                pass
            else:
                logger.error(f"Audio playback error: {e}")
        except Exception as e:
            logger.error(f"Failed to play audio {file_path}: {e}")
        finally:
            with self._lock:
                if self._current_stream:
                    self._current_stream.stop()
                    self._current_stream.close()
                    self._current_stream = None

    def interrupt(self):
        """Immediately stops the current playback."""
        with self._lock:
            if self._current_stream and self._current_stream.active:
                logger.debug("Interrupting audio playback.")
                self._current_stream.abort()
                self._current_stream.close()
                self._current_stream = None

# NO MODULE-LEVEL SINGLETON — created in build_app()
