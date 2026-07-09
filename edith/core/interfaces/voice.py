from abc import ABC, abstractmethod
from edith.ai.models import HealthStatus

class IVoiceManager(ABC):
    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def health_check(self) -> HealthStatus:
        pass

    @abstractmethod
    def speak(self, text: str, priority: str = "normal") -> None:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass
