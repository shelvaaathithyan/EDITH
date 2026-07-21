import time
from typing import Optional
from edith.utils.logger import logger
from edith.ai.providers.factory import ProviderFactory
from edith.ai.validator import ResponseValidator
from edith.ai.parser import ResponseParser
from edith.ai.prompts import get_system_prompt
from edith.ai.models import PlannerResponse, ResponseMetadata, ErrorResponse, HealthStatus
from edith.ai.exceptions import JSONValidationError, ProviderError

class Planner:
    def __init__(self):
        self.provider = ProviderFactory.get_provider()
        self.validator = ResponseValidator()
        self.parser = ResponseParser()
        self._initialized = False

    # ── Lifecycle ────────────────────────────────────────────────

    def initialize(self):
        """
        Initializes the underlying LLM provider.
        Must be called before plan() — enforced by the _initialized guard.
        Propagates ProviderError / ModelMissingError on failure.
        """
        if self._initialized:
            logger.warning("[Planner] Already initialized, skipping.")
            return

        logger.info("[Planner] initialize() START")
        self.provider.initialize()
        self._initialized = True
        logger.info(f"[Planner] initialize() END | provider={self.provider.__class__.__name__} | model={getattr(self.provider, 'resolved_model', 'unknown')}")

    def health_check(self) -> HealthStatus:
        """Delegates health check to the underlying provider."""
        return self.provider.health_check()

    def shutdown(self):
        """Shuts down the underlying provider."""
        logger.info("[Planner] shutdown()")
        if hasattr(self.provider, 'shutdown'):
            self.provider.shutdown()

    # ── Planning ─────────────────────────────────────────────────

    def plan(self, user_input: str) -> PlannerResponse:
        """
        Receives user natural language and returns a structured ExecutionPlan or ChatResponse.
        Retries up to 2 times if JSON validation fails.
        """
        # Guard: refuse to plan if provider was never initialized
        if not self._initialized:
            logger.error("[Planner] plan() called before initialize(). Returning error.")
            return self._create_error_response(
                "Planner was not initialized. The AI provider failed to start.",
                time.time()
            )

        logger.info(f"[Planner] plan() START | input='{user_input[:80]}...'")
        system_prompt = get_system_prompt()
        max_retries = 2

        # We might need to feedback the validation error to the LLM
        current_prompt = user_input

        for attempt in range(max_retries + 1):
            start_time = time.time()
            try:
                # 1. Ask Provider for plan
                logger.info(f"[Planner] Attempt {attempt+1}/{max_retries+1} | model={getattr(self.provider, 'resolved_model', 'unknown')}")
                raw_json = self.provider.plan(current_prompt, system_prompt)
                latency = time.time() - start_time
                logger.info(f"[Planner] Provider responded | latency={latency:.3f}s | response_length={len(raw_json)}")

                # 2. Validate format against schema
                validated_dict = self.validator.validate_raw(raw_json)

                # 3. Create metadata
                metadata = ResponseMetadata(
                    provider=self.provider.__class__.__name__,
                    model=getattr(self.provider, 'resolved_model', 'unknown'),
                    latency=round(latency, 3),
                    created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                )

                # 4. Parse into typed Pydantic models
                result = self.parser.parse(validated_dict, metadata)
                logger.info(f"[Planner] plan() END | type={result.data.type} | latency={latency:.3f}s")
                return result

            except JSONValidationError as e:
                logger.warning(f"[Planner] Validation Error (Attempt {attempt+1}/{max_retries+1}): {e}")
                if attempt < max_retries:
                    # Provide corrective feedback to the LLM
                    current_prompt = f"{user_input}\n\nYour last response failed validation with error: {e}. Please fix it and return ONLY valid JSON."
                else:
                    return self._create_error_response(f"Failed to generate valid JSON after retries: {e}", start_time)
            except ProviderError as e:
                logger.error(f"[Planner] Provider Error: {e}")
                return self._create_error_response(str(e), start_time)
            except Exception as e:
                logger.error(f"[Planner] Unexpected Error: {e}")
                return self._create_error_response("An unexpected error occurred during planning.", start_time)

    def _create_error_response(self, message: str, start_time: float) -> PlannerResponse:
        latency = round(time.time() - start_time, 3)
        metadata = ResponseMetadata(
            provider=self.provider.__class__.__name__,
            model=getattr(self.provider, 'resolved_model', 'unknown'),
            latency=latency,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        return PlannerResponse(
            data=ErrorResponse(message=message),
            metadata=metadata
        )
