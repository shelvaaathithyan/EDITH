from abc import ABC, abstractmethod
from typing import Dict, Any, List
from edith.ai.models import ExecutionPlan

class IToolExecutor(ABC):
    @abstractmethod
    def execute(self, plan: ExecutionPlan) -> str:
        """Executes a plan and returns a summary of the result."""
        pass
