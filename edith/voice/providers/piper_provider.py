import os
import time
import requests
import tempfile
import threading
from pathlib import Path
import wave
from piper.config import SynthesisConfig
from piper.voice import PiperVoice
from edith.config.settings import settings
from edith.utils.logger import logger
from edith.voice.providers.base_provider import BaseTTSProvider

VOICES_DIR = Path("edith/assets/voices")

class PiperProvider(BaseTTSProvider):
    def __init__(self, audio_player=None):
        self.voice = None
        self._lock = threading.Lock()
        self._audio_player = audio_player

    def _get_model_name(self) -> str:
        profile_name = settings.voice_profile
        profile = settings.voice_profiles.get(profile_name)
        if not profile:
            logger.warning(f"Voice profile {profile_name} not found, defaulting to edith_default.")
            return "en_US-lessac-medium"
        return profile.model_name

    def initialize(self):
        VOICES_DIR.mkdir(parents=True, exist_ok=True)
        model_name = self._get_model_name()
        
        onnx_path = VOICES_DIR / f"{model_name}.onnx"
        json_path = VOICES_DIR / f"{model_name}.onnx.json"

        if not onnx_path.exists() or not json_path.exists():
            logger.info(f"Piper model {model_name} not found. Downloading...")
            self._download_model(model_name, onnx_path, json_path)
            
        logger.info(f"Loading Piper voice model: {model_name}")
        self.voice = PiperVoice.load(str(onnx_path), str(json_path))

    def _download_model(self, model_name: str, onnx_path: Path, json_path: Path):
        base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/{model_name.split('-')[1]}/{model_name.split('-')[2]}/{model_name}"
        
        onnx_url = f"{base_url}.onnx?download=true"
        json_url = f"{base_url}.onnx.json?download=true"
        
        try:
            logger.info("Downloading ONNX file...")
            r_onnx = requests.get(onnx_url, stream=True)
            r_onnx.raise_for_status()
            with open(onnx_path, 'wb') as f:
                for chunk in r_onnx.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info("Downloading JSON config...")
            r_json = requests.get(json_url, stream=True)
            r_json.raise_for_status()
            with open(json_path, 'wb') as f:
                for chunk in r_json.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("Download complete.")
        except Exception as e:
            logger.error(f"Failed to download Piper model: {e}")
            if onnx_path.exists(): os.remove(onnx_path)
            if json_path.exists(): os.remove(json_path)

    def speak(self, text: str, interruptible: bool = True):
        logger.info("ENTER PiperProvider.speak()")
        if not self.voice:
            self.initialize()

        if not text.strip():
            logger.info("EXIT PiperProvider.speak() [Empty text]")
            return

        if not self._audio_player:
            logger.error("[PiperProvider] No audio_player set, cannot play TTS.")
            logger.info("EXIT PiperProvider.speak() [No audio player]")
            return

        with self._lock:
            wav_path = "s:/EDITH/temp/last_tts.wav"
            try:
                os.makedirs(os.path.dirname(wav_path), exist_ok=True)
                logger.info(f"[PiperProvider] Synthesis START | text='{text[:60]}...' | length={len(text)}")
                synth_start = time.time()
                
                # Synthesize text to WAV using Piper
                with wave.open(wav_path, "wb") as wav_file:
                    self.voice.synthesize_wav(
                        text, 
                        wav_file, 
                        syn_config=SynthesisConfig(length_scale=1.0/settings.speech_speed)
                    )

                synth_duration = time.time() - synth_start
                wav_size = os.path.getsize(wav_path) if os.path.exists(wav_path) else 0
                
                # Verify WAV and read properties
                import soundfile as sf
                import numpy as np
                try:
                    data, fs = sf.read(wav_path)
                    channels = data.ndim if len(data.shape) > 1 else 1
                    samples = len(data)
                    duration = samples / fs
                    peak_amp = np.max(np.abs(data)) if len(data) > 0 else 0
                    rms_amp = np.sqrt(np.mean(data**2)) if len(data) > 0 else 0
                    
                    logger.info(f"[PiperProvider] WAV VERIFIED | Path: {wav_path} | Size: {wav_size} bytes")
                    logger.info(f"[PiperProvider] WAV PROPS    | Duration: {duration:.3f}s | Sample Rate: {fs}Hz | Channels: {channels}")
                    logger.info(f"[PiperProvider] WAV AUDIO    | Samples: {samples} | Peak: {peak_amp:.4f} | RMS: {rms_amp:.4f}")
                    
                    if samples == 0 or peak_amp == 0:
                        logger.error("[PiperProvider] WAV file is SILENT! (Empty or zero amplitude)")
                except Exception as e:
                    logger.error(f"[PiperProvider] Failed to verify WAV file: {e}")

                logger.info(f"[PiperProvider] Synthesis END | duration={synth_duration:.3f}s | wav_size={wav_size} bytes")

                # Play the WAV file using sounddevice (this blocks until done)
                play_start = time.time()
                self._audio_player.play_wav(wav_path, block=True)
                play_duration = time.time() - play_start
                logger.info(f"[PiperProvider] Playback END | duration={play_duration:.3f}s")

            except Exception as e:
                logger.error(f"Piper synthesis error: {e}")
            finally:
                pass # Do not delete wav_path
        logger.info("EXIT PiperProvider.speak()")

    def interrupt(self):
        if self._audio_player:
            self._audio_player.interrupt()

    def stop(self):
        self.interrupt()
        self.voice = None
