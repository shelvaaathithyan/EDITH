from abc import ABC, abstractmethod
from edith.ai.models import PlannerResponse, HealthStatus

class IPlanner(ABC):
    @abstractmethod
    def plan(self, user_input: str) -> PlannerResponse:
        pass

    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def health_check(self) -> HealthStatus:
        pass
