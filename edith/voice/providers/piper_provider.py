import os
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
from edith.voice.audio import audio_player

VOICES_DIR = Path("edith/assets/voices")

class PiperProvider(BaseTTSProvider):
    def __init__(self):
        self.voice = None
        self._lock = threading.Lock()

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
        if not self.voice:
            self.initialize()

        if not text.strip():
            return

        with self._lock:
            try:
                # Generate a temporary WAV file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                    wav_path = temp_wav.name
                
                # Synthesize text to WAV using Piper
                with wave.open(wav_path, "wb") as wav_file:
                    self.voice.synthesize_wav(
                        text, 
                        wav_file, 
                        syn_config=SynthesisConfig(length_scale=1.0/settings.speech_speed)
                    )

                # Play the WAV file using sounddevice (this blocks until done)
                audio_player.play_wav(wav_path, block=True)

            except Exception as e:
                logger.error(f"Piper synthesis error: {e}")
            finally:
                if os.path.exists(wav_path):
                    try:
                        os.remove(wav_path)
                    except Exception as e:
                        logger.error(f"Failed to delete temp WAV {wav_path}: {e}")

    def interrupt(self):
        audio_player.interrupt()

    def stop(self):
        self.interrupt()
        self.voice = None
