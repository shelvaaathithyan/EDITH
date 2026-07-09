from abc import ABC, abstractmethod
from typing import Dict, List, Any
from edith.ai.models import HealthStatus

class LLMProvider(ABC):
    @abstractmethod
    def initialize(self):
        """Initializes the provider and verifies configuration."""
        pass

    @abstractmethod
    def plan(self, user_prompt: str, system_prompt: str) -> str:
        """
        Sends the prompt and system prompt to the LLM and returns the raw response string.
        Must enforce JSON formatting if the provider supports it natively.
        """
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Sends a list of messages (role, content) for open-ended chat."""
        pass

    @abstractmethod
    def health_check(self) -> HealthStatus:
        """Verifies the health and connectivity of the provider."""
        pass

    @abstractmethod
    def shutdown(self):
        """Cleans up resources."""
        pass
