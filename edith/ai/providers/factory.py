from edith.config.settings import settings
from edith.ai.providers.base_provider import LLMProvider
from edith.ai.providers.ollama_provider import OllamaProvider
from edith.utils.logger import logger

class ProviderFactory:
    @staticmethod
    def get_provider() -> LLMProvider:
        provider_name = settings.ai_provider.lower()
        if provider_name == "ollama":
            return OllamaProvider()
        else:
            logger.warning(f"AI Provider '{provider_name}' not supported yet. Defaulting to Ollama.")
            return OllamaProvider()
