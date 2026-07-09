from edith.config.settings import settings
from edith.voice.providers.base_provider import BaseTTSProvider
from edith.voice.providers.piper_provider import PiperProvider
from edith.utils.logger import logger

class VoiceProviderFactory:
    @staticmethod
    def get_provider() -> BaseTTSProvider:
        engine = settings.voice_engine.lower()
        if engine == "piper":
            return PiperProvider()
        # Later add ElevenLabsProvider, etc.
        else:
            logger.warning(f"Voice engine {engine} not supported. Defaulting to Piper.")
            return PiperProvider()
