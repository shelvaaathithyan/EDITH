from abc import ABC, abstractmethod
from typing import Dict, Any, List
from edith.ai.models import ExecutionPlan, ToolResult

class IToolExecutor(ABC):
    @abstractmethod
    def execute(self, plan: ExecutionPlan) -> ToolResult:
        """Executes a plan and returns a structured ToolResult."""
        pass
