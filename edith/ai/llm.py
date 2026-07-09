import json
from typing import Dict, Any
from openai import OpenAI
from edith.config.settings import settings
from edith.utils.logger import logger
from edith.ai.prompts import INTENT_SYSTEM_PROMPT

class LLMClient:
    def __init__(self):
        self.client = None
        if settings.api_key:
            self.client = OpenAI(api_key=settings.api_key)

    def parse_intent(self, text: str) -> Dict[str, Any]:
        """Sends the user text to LLM and returns the parsed JSON intent."""
        if not self.client:
            logger.error("OpenAI API key is missing. Cannot parse intent.")
            return {"intent": "error", "response": "My API key is missing. Please configure it in settings."}

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o", # use a smart model for accurate JSON
                messages=[
                    {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            return {"intent": "error", "response": "Empty response from LLM."}
        except Exception as e:
            logger.error(f"Error parsing intent: {e}")
            return {"intent": "error", "response": f"I encountered an error trying to understand that: {e}"}

llm_client = LLMClient()
