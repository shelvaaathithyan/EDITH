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
        """Plays a WAV file synchronously using sd.play() and sd.wait()."""
        logger.info(f"ENTER AudioPlayer.play_wav() | file={file_path}")
        
        # --- Phase 3: Verify WAV Loading ---
        logger.info("Loading WAV...")
        import os
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"WAV file does not exist: {file_path}")
            
        file_size = os.path.getsize(file_path)
        try:
            data, fs = sf.read(file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to decode WAV: {e}")
            
        logger.info("Loaded WAV successfully")
        
        channels = data.ndim if len(data.shape) > 1 else 1
        samples = len(data)
        duration = samples / fs if fs > 0 else 0
        peak_amp = np.max(np.abs(data)) if samples > 0 else 0
        rms_amp = np.sqrt(np.mean(data**2)) if samples > 0 else 0
        
        logger.info(f"[WAV Diagnostics] Path: {file_path}")
        logger.info(f"[WAV Diagnostics] Exists: True")
        logger.info(f"[WAV Diagnostics] File size: {file_size} bytes")
        logger.info(f"[WAV Diagnostics] Duration: {duration:.3f}s")
        logger.info(f"[WAV Diagnostics] Channels: {channels}")
        logger.info(f"[WAV Diagnostics] Sample rate: {fs}")
        logger.info(f"[WAV Diagnostics] dtype: {data.dtype}")
        logger.info(f"[WAV Diagnostics] shape: {data.shape}")
        logger.info(f"[WAV Diagnostics] Minimum amplitude: {np.min(data) if samples > 0 else 0:.4f}")
        logger.info(f"[WAV Diagnostics] Maximum amplitude: {peak_amp:.4f}")
        logger.info(f"[WAV Diagnostics] RMS amplitude: {rms_amp:.4f}")
        
        if samples == 0 or peak_amp == 0:
            raise ValueError(f"Invalid WAV: Samples={samples}, Peak Amplitude={peak_amp}")

        # Apply volume setting
        if settings.volume != 1.0:
            data = data * settings.volume

        # Ensure data is float32
        data = np.asarray(data, dtype=np.float32)

        with self._lock:
            # --- Phase 7: Windows Device Verification ---
            devices = sd.query_devices()
            default_device_idx = sd.default.device[1]
            
            logger.info("=== Audio Output Devices ===")
            for idx, dev in enumerate(devices):
                if dev['max_output_channels'] > 0:
                    is_default = (idx == default_device_idx)
                    marker = "[DEFAULT/SELECTED]" if is_default else ""
                    logger.info(f"[{idx}] {dev['name']} {marker} | HostAPI: {dev.get('hostapi')} | SR: {dev['default_samplerate']} | Channels: {dev['max_output_channels']}")
            logger.info("============================")
            
            selected_dev = devices[default_device_idx]
            
            # --- Phase 4: Verify AudioPlayer (pre-play) ---
            logger.info(f"[AudioPlayer] Selected device index: {default_device_idx}")
            logger.info(f"[AudioPlayer] Selected device name: {selected_dev['name']}")
            logger.info(f"[AudioPlayer] Host API: {selected_dev.get('hostapi')}")
            logger.info(f"[AudioPlayer] Samplerate: {fs}")
            logger.info(f"[AudioPlayer] Blocksize: Not explicitly set (default)")
            logger.info(f"[AudioPlayer] Latency: {selected_dev.get('default_low_output_latency')} / {selected_dev.get('default_high_output_latency')}")
            logger.info(f"[AudioPlayer] dtype: {data.dtype}")
            logger.info(f"[AudioPlayer] Channels: {channels}")
            logger.info(f"[AudioPlayer] Shape: {data.shape}")
            logger.info(f"[AudioPlayer] Frames: {samples}")

            try:
                # --- Phase 8: Blocking Playback ---
                logger.info("Playback Started")
                logger.info("Calling sd.play()")
                sd.play(data, samplerate=fs, device=default_device_idx)
                logger.info("Returned from sd.play()")
                
                logger.info("Entering sd.wait()")
                sd.wait()
                logger.info("Returned from sd.wait()")
                logger.info(f"Playback Finished | Playback Duration: {duration:.3f}s")
                
            except Exception as e:
                logger.error(f"Failed to play audio {file_path}: {e}")
                
        logger.info("EXIT AudioPlayer.play_wav()")

    def interrupt(self):
        """Immediately stops the current playback."""
        with self._lock:
            if self._current_stream and self._current_stream.active:
                logger.debug("Interrupting audio playback.")
                self._current_stream.abort()
                self._current_stream.close()
                self._current_stream = None

# NO MODULE-LEVEL SINGLETON — created in build_app()
