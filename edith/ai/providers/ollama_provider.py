import time
import httpx
from typing import Dict, List, Any, Optional
from edith.config.settings import settings
from edith.utils.logger import logger
from edith.ai.models import HealthStatus
from edith.ai.exceptions import ProviderError, ModelMissingError
from edith.ai.providers.base_provider import LLMProvider

OLLAMA_API_URL = "http://localhost:11434/api"

class OllamaProvider(LLMProvider):

    def __init__(self):
        self.configured_model: str = settings.ai_model
        self.resolved_model: Optional[str] = None
        self.installed_models: List[str] = []
        self.timeout = settings.ai_timeout
        self.client = httpx.Client(timeout=self.timeout)
        self._initialized = False

    # ── Lifecycle ────────────────────────────────────────────────

    def resolve_model(self) -> str:
        """
        Queries Ollama /api/tags, resolves the configured model alias
        to an exact installed model name, and stores the result.
        Raises ProviderError if resolution fails.
        """
        logger.info(f"[OllamaProvider] resolve_model() START | configured_model={self.configured_model}")

        try:
            r = self.client.get(f"{OLLAMA_API_URL}/tags")
            r.raise_for_status()
            self.installed_models = [m.get("name") for m in r.json().get("models", [])]
            logger.info(f"[OllamaProvider] Installed models: {self.installed_models}")
        except httpx.RequestError as e:
            raise ProviderError(f"Cannot connect to Ollama at {OLLAMA_API_URL}: {e}")
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"Ollama /api/tags returned HTTP {e.response.status_code}: {e.response.text}")

        if not self.installed_models:
            raise ProviderError("Ollama is running but has no models installed. Run: ollama pull <model>")

        # 1. Exact match
        if self.configured_model in self.installed_models:
            self.resolved_model = self.configured_model
            logger.info(f"[OllamaProvider] Exact match: {self.resolved_model}")
            return self.resolved_model

        # 2. Alias resolution: strip ":latest" and match prefix
        base_name = self.configured_model.replace(":latest", "")
        matches = [m for m in self.installed_models if m.startswith(base_name)]

        if len(matches) == 1:
            self.resolved_model = matches[0]
            logger.info(f"[OllamaProvider] Alias resolved: {self.configured_model} -> {self.resolved_model}")
            return self.resolved_model
        elif len(matches) > 1:
            raise ProviderError(
                f"Ambiguous model match for '{self.configured_model}'. "
                f"Found: {matches}. Please specify the exact model in settings."
            )
        else:
            raise ModelMissingError(
                f"Ollama model '{self.configured_model}' is not installed. "
                f"Installed models: {self.installed_models}. "
                f"Run: ollama pull {self.configured_model}"
            )

    def initialize(self):
        """
        Full initialization lifecycle:
        1. resolve_model()  — find the exact installed model
        2. health_check()   — verify Ollama server + inference
        Raises ProviderError or ModelMissingError on failure.
        """
        if self._initialized:
            logger.warning("[OllamaProvider] Already initialized, skipping.")
            return

        logger.info("[OllamaProvider] initialize() START")
        logger.info(f"  Base URL:     {OLLAMA_API_URL}")
        logger.info(f"  Endpoint:     {OLLAMA_API_URL}/generate")
        logger.info(f"  Model:        {self.configured_model}")
        logger.info(f"  Timeout:      {self.timeout}s")
        logger.info(f"  Temperature:  {settings.ai_temperature}")
        logger.info(f"  Max Tokens:   {settings.ai_max_tokens}")

        # Step 1: Resolve model
        self.resolve_model()

        # Step 2: Health check (inference test)
        health = self.health_check()
        if health.status != "healthy":
            raise ProviderError(f"Ollama health check failed after model resolution: {health.error}")

        self._initialized = True
        logger.info(f"[OllamaProvider] initialize() END | resolved_model={self.resolved_model}")

    # ── Inference ────────────────────────────────────────────────

    def _ensure_initialized(self):
        """Guard: refuse inference if provider was never initialized."""
        if not self._initialized or not self.resolved_model:
            raise ProviderError(
                f"OllamaProvider.plan()/chat() called before initialize(). "
                f"resolved_model={self.resolved_model}, initialized={self._initialized}"
            )

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

    def plan(self, user_prompt: str, system_prompt: str) -> str:
        """Sends prompt to Ollama enforcing JSON format."""
        self._ensure_initialized()

        start_time = time.time()
        payload = {
            "model": self.resolved_model,
            "system": system_prompt,
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": settings.ai_temperature,
                "num_predict": settings.ai_max_tokens
            }
        }

        logger.info(f"[OllamaProvider] plan() START | model={self.resolved_model}")
        logger.debug(f"  POST URL: {OLLAMA_API_URL}/generate")
        logger.debug(f"  Prompt length: {len(user_prompt)}")
        logger.debug(f"  System prompt length: {len(system_prompt)}")

        try:
            response = self.client.post(f"{OLLAMA_API_URL}/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            result = data.get("response", "")
            latency = time.time() - start_time
            logger.info(f"[OllamaProvider] plan() END | latency={latency:.3f}s | response_length={len(result)}")
            return result

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
        self._ensure_initialized()

        payload = {
            "model": self.resolved_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": settings.ai_temperature,
                "num_predict": settings.ai_max_tokens
            }
        }

        logger.info(f"[OllamaProvider] chat() START | model={self.resolved_model} | messages={len(messages)}")

        try:
            response = self.client.post(f"{OLLAMA_API_URL}/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            result = data.get("message", {}).get("content", "")
            logger.info(f"[OllamaProvider] chat() END | response_length={len(result)}")
            return result
        except httpx.HTTPStatusError as e:
            self._log_http_error(e, payload)
            raise ProviderError(f"Ollama chat HTTP {e.response.status_code} Error: {e.response.text}")
        except Exception as e:
            raise ProviderError(f"Ollama chat error: {e}")

    # ── Health ───────────────────────────────────────────────────

    def health_check(self) -> HealthStatus:
        start_time = time.time()
        details = {
            "ollama_running": False,
            "model_installed": False,
            "inference_test": False,
            "configured_model": self.configured_model,
            "resolved_model": self.resolved_model,
            "installed_models": self.installed_models,
        }

        model_for_test = self.resolved_model or self.configured_model

        try:
            # 1. Check if Ollama is running
            r = self.client.get("http://localhost:11434/")
            if r.status_code == 200:
                details["ollama_running"] = True

            # 2. Check if model is resolved / installed
            if self.resolved_model and self.resolved_model in self.installed_models:
                details["model_installed"] = True
            else:
                # Try resolution if not yet done
                try:
                    r = self.client.get(f"{OLLAMA_API_URL}/tags")
                    r.raise_for_status()
                    self.installed_models = [m.get("name") for m in r.json().get("models", [])]
                    details["installed_models"] = self.installed_models

                    if model_for_test in self.installed_models:
                        details["model_installed"] = True
                    else:
                        base_name = model_for_test.replace(":latest", "")
                        matches = [m for m in self.installed_models if m.startswith(base_name)]
                        if matches:
                            details["model_installed"] = True
                            model_for_test = matches[0]
                        else:
                            return HealthStatus(
                                status="unhealthy", provider="ollama", model=model_for_test,
                                error="Model missing", details=details
                            )
                except Exception:
                    pass

            # 3. Inference test
            test_payload = {"model": model_for_test, "prompt": "Hello", "stream": False, "options": {"num_predict": 2}}
            logger.info(f"[OllamaProvider] Running inference test against {model_for_test}...")
            r = self.client.post(f"{OLLAMA_API_URL}/generate", json=test_payload, timeout=120.0)

            try:
                r.raise_for_status()
                details["inference_test"] = True
                logger.info("[OllamaProvider] Inference test passed.")
            except httpx.HTTPStatusError as e:
                self._log_http_error(e, test_payload)
                return HealthStatus(
                    status="unhealthy", provider="ollama", model=model_for_test,
                    error=f"Inference failed with {e.response.status_code}", details=details
                )

            latency = time.time() - start_time
            return HealthStatus(
                status="healthy", provider="ollama", model=model_for_test,
                latency=latency, details=details
            )

        except httpx.RequestError as e:
            return HealthStatus(
                status="unhealthy", provider="ollama", model=model_for_test,
                error=f"Connection refused: {e}", details=details
            )
        except ProviderError as e:
            return HealthStatus(
                status="unhealthy", provider="ollama", model=model_for_test,
                error=str(e), details=details
            )
        except Exception as e:
            return HealthStatus(
                status="unhealthy", provider="ollama", model=model_for_test,
                error=f"Unexpected error: {e}", details=details
            )

    # ── Shutdown ─────────────────────────────────────────────────

    def shutdown(self):
        logger.info("[OllamaProvider] Shutting down HTTP client.")
        self.client.close()
