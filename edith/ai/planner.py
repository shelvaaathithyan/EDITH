import time
from typing import Optional
from edith.utils.logger import logger
from edith.ai.providers.factory import ProviderFactory
from edith.ai.validator import ResponseValidator
from edith.ai.parser import ResponseParser
from edith.ai.prompts import get_system_prompt
from edith.ai.models import PlannerResponse, ResponseMetadata, ErrorResponse
from edith.ai.exceptions import JSONValidationError, ProviderError

class Planner:
    def __init__(self):
        self.provider = ProviderFactory.get_provider()
        self.validator = ResponseValidator()
        self.parser = ResponseParser()
        
    def plan(self, user_input: str) -> PlannerResponse:
        """
        Receives user natural language and returns a structured ExecutionPlan or ChatResponse.
        Retries up to 2 times if JSON validation fails.
        """
        logger.info(f"Planner processing input: '{user_input}'")
        system_prompt = get_system_prompt()
        max_retries = 2
        
        # We might need to feedback the validation error to the LLM
        current_prompt = user_input
        
        for attempt in range(max_retries + 1):
            start_time = time.time()
            try:
                # 1. Ask Provider for plan
                raw_json = self.provider.plan(current_prompt, system_prompt)
                latency = time.time() - start_time
                
                # 2. Validate format against schema
                validated_dict = self.validator.validate_raw(raw_json)
                
                # 3. Create metadata
                metadata = ResponseMetadata(
                    provider=self.provider.__class__.__name__,
                    model=getattr(self.provider, 'model', 'unknown'),
                    latency=round(latency, 3),
                    created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                )
                
                # 4. Parse into typed Pydantic models
                return self.parser.parse(validated_dict, metadata)

            except JSONValidationError as e:
                logger.warning(f"Planner Validation Error (Attempt {attempt+1}/{max_retries+1}): {e}")
                if attempt < max_retries:
                    # Provide corrective feedback to the LLM
                    current_prompt = f"{user_input}\n\nYour last response failed validation with error: {e}. Please fix it and return ONLY valid JSON."
                else:
                    return self._create_error_response(f"Failed to generate valid JSON after retries: {e}", start_time)
            except ProviderError as e:
                logger.error(f"Planner Provider Error: {e}")
                return self._create_error_response(str(e), start_time)
            except Exception as e:
                logger.error(f"Planner Unexpected Error: {e}")
                return self._create_error_response("An unexpected error occurred during planning.", start_time)
                
    def _create_error_response(self, message: str, start_time: float) -> PlannerResponse:
        latency = round(time.time() - start_time, 3)
        metadata = ResponseMetadata(
            provider=self.provider.__class__.__name__,
            model=getattr(self.provider, 'model', 'unknown'),
            latency=latency,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        return PlannerResponse(
            data=ErrorResponse(message=message),
            metadata=metadata
        )

planner = Planner()
