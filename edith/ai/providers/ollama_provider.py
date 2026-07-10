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
    _resolved_model = None

    def __init__(self):
        self.model = OllamaProvider._resolved_model or settings.ai_model
        self.timeout = settings.ai_timeout
        self.client = httpx.Client(timeout=self.timeout)

    def _log_http_error(self, e: httpx.HTTPStatusError, payload: dict):
        logger.error(f"Ollama HTTP Error: {e.response.status_code}")
        logger.error(f"URL: {e.request.url}")
        logger.error(f"Method: {e.request.method}")
        logger.error(f"Request JSON: {payload}")
        logger.error(f"Response Headers: {e.response.headers}")
        logger.error(f"Raw Response Body: {e.response.text}")
        try:
            logger.error(f"Parsed JSON: {e.response.json()}")
        except Exception:
            pass

    def initialize(self):
        logger.info("Initializing Ollama Provider...")
        logger.info(f"Configured Base URL: {OLLAMA_API_URL}")
        logger.info(f"Configured Endpoint: {OLLAMA_API_URL}/generate")
        logger.info(f"Configured Model: {self.model}")
        logger.info(f"Configured Timeout: {self.timeout}s")
        logger.info(f"Configured Temperature: {settings.ai_temperature}")
        logger.info(f"Configured Max Tokens: {settings.ai_max_tokens}")
        
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
        
        logger.info(f"Configured Model: {settings.ai_model}")
        logger.info(f"Resolved Model: {OllamaProvider._resolved_model}")
        logger.info(f"Request Model: {self.model}")
        logger.debug(f"POST URL: {OLLAMA_API_URL}/generate")
        logger.debug(f"Headers: {self.client.headers}")
        logger.debug(f"JSON Payload: {payload}")
        logger.debug(f"Prompt Length: {len(user_prompt)}")
        logger.debug(f"System Prompt Length: {len(system_prompt)}")
        
        try:
            response = self.client.post(f"{OLLAMA_API_URL}/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
            
        except httpx.HTTPStatusError as e:
            self._log_http_error(e, payload)
            raise ProviderError(f"Ollama HTTP {e.response.status_code} Error: {e.response.text}")
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
        
        logger.info(f"Configured Model: {settings.ai_model}")
        logger.info(f"Resolved Model: {OllamaProvider._resolved_model}")
        logger.info(f"Request Model: {self.model}")
        
        try:
            response = self.client.post(f"{OLLAMA_API_URL}/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except httpx.HTTPStatusError as e:
            self._log_http_error(e, payload)
            raise ProviderError(f"Ollama chat HTTP {e.response.status_code} Error: {e.response.text}")
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
            
            logger.info(f"Configured Model: {self.model}")
            logger.info(f"Installed Models: {models}")
            
            if self.model in models:
                details["model_installed"] = True
                OllamaProvider._resolved_model = self.model
                logger.info(f"Resolved Model: {self.model}")
            else:
                base_model = self.model.replace(":latest", "")
                matches = [m for m in models if m.startswith(base_model)]
                if len(matches) == 1:
                    self.model = matches[0]
                    OllamaProvider._resolved_model = self.model
                    details["model_installed"] = True
                    logger.info(f"Resolved Model: {self.model}")
                elif len(matches) > 1:
                    raise ProviderError(f"Ambiguous model match for '{self.model}'. Found: {matches}. Please specify exact model in settings.")
                else:
                    return HealthStatus(
                        status="unhealthy", provider="ollama", model=self.model,
                        error="Model missing", details=details
                    )
                
            # 3. Inference test
            test_payload = {"model": self.model, "prompt": "Hello", "stream": False, "options": {"num_predict": 2}}
            logger.info(f"Running startup inference test against {self.model}...")
            r = self.client.post(f"{OLLAMA_API_URL}/generate", json=test_payload, timeout=120.0)
            
            try:
                r.raise_for_status()
                details["inference_test"] = True
                logger.info("Startup inference test successful.")
            except httpx.HTTPStatusError as e:
                self._log_http_error(e, test_payload)
                return HealthStatus(
                    status="unhealthy", provider="ollama", model=self.model,
                    error=f"Inference failed with {e.response.status_code}", details=details
                )
            
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
        except ProviderError as e:
            return HealthStatus(
                status="unhealthy", provider="ollama", model=self.model,
                error=str(e), details=details
            )
        except Exception as e:
            return HealthStatus(
                status="unhealthy", provider="ollama", model=self.model,
                error=f"Unexpected error: {e}", details=details
            )

    def shutdown(self):
        self.client.close()
