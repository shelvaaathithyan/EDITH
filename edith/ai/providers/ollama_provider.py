import time
import httpx
from typing import Dict, List, Any
from edith.config.settings import settings
from edith.utils.logger import logger
from edith.ai.models import HealthStatus
from edith.ai.exceptions import ProviderError, ModelMissingError
from edith.ai.providers.base_provider import LLMProvider

OLLAMA_API_URL = "http://localhost:11434/api"

class OllamaProvider(LLMProvider):
    def __init__(self):
        self.model = settings.ai_model
        self.timeout = settings.ai_timeout
        self.client = httpx.Client(timeout=self.timeout)

    def initialize(self):
        logger.info(f"Initializing Ollama Provider with model: {self.model}")
        health = self.health_check()
        if health.status != "healthy":
            if health.error == "Model missing":
                raise ModelMissingError(f"Ollama model '{self.model}' is not installed.")
            raise ProviderError(f"Ollama is unhealthy: {health.error}")

    def plan(self, user_prompt: str, system_prompt: str) -> str:
        """Sends prompt to Ollama enforcing JSON format."""
        start_time = time.time()
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": settings.ai_temperature,
                "num_predict": settings.ai_max_tokens
            }
        }
        
        try:
            response = self.client.post(f"{OLLAMA_API_URL}/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            # We can log latency here or let Planner handle metadata
            return data.get("response", "")
            
        except httpx.RequestError as e:
            logger.error(f"Ollama connection error: {e}")
            raise ProviderError(f"Failed to connect to Ollama: {e}")
        except Exception as e:
            logger.error(f"Ollama unexpected error: {e}")
            raise ProviderError(f"Ollama error: {e}")

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """For conversational chat, potentially without JSON enforcement."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": settings.ai_temperature,
                "num_predict": settings.ai_max_tokens
            }
        }
        
        try:
            response = self.client.post(f"{OLLAMA_API_URL}/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            raise ProviderError(f"Ollama chat error: {e}")

    def health_check(self) -> HealthStatus:
        start_time = time.time()
        details = {
            "ollama_running": False,
            "model_installed": False,
            "inference_test": False
        }
        
        try:
            # 1. Check if Ollama is running
            r = self.client.get("http://localhost:11434/")
            if r.status_code == 200:
                details["ollama_running"] = True
            
            # 2. Check if model is installed
            r = self.client.get(f"{OLLAMA_API_URL}/tags")
            r.raise_for_status()
            models = [m.get("name") for m in r.json().get("models", [])]
            
            # Ollama tags might include :latest, so we do a substring or exact check
            if any(self.model in m for m in models):
                details["model_installed"] = True
            else:
                return HealthStatus(
                    status="unhealthy", provider="ollama", model=self.model,
                    error="Model missing", details=details
                )
                
            # 3. Inference test
            test_payload = {"model": self.model, "prompt": "hi", "stream": False, "options": {"num_predict": 2}}
            self.client.post(f"{OLLAMA_API_URL}/generate", json=test_payload)
            details["inference_test"] = True
            
            latency = time.time() - start_time
            return HealthStatus(
                status="healthy", provider="ollama", model=self.model,
                latency=latency, details=details
            )
            
        except httpx.RequestError as e:
            return HealthStatus(
                status="unhealthy", provider="ollama", model=self.model,
                error=f"Connection refused: {e}", details=details
            )
        except Exception as e:
            return HealthStatus(
                status="unhealthy", provider="ollama", model=self.model,
                error=f"Unexpected error: {e}", details=details
            )

    def shutdown(self):
        self.client.close()
