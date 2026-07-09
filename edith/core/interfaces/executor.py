from abc import ABC, abstractmethod
from typing import Union
from edith.ai.models import ExecutionPlan, ResolvedExecutionPlan, ToolResult

class IToolExecutor(ABC):
    @abstractmethod
    def execute(self, plan: Union[ExecutionPlan, ResolvedExecutionPlan]) -> ToolResult:
        """Executes a plan and returns a structured ToolResult."""
        pass
