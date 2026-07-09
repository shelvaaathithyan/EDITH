from abc import ABC, abstractmethod
from typing import Union
from edith.ai.models import ExecutionPlan, ResolvedExecutionPlan

class IPermissionManager(ABC):
    @abstractmethod
    def evaluate_plan(self, plan: Union[ExecutionPlan, ResolvedExecutionPlan]) -> bool:
        """
        Evaluates a plan against the policy engine.
        Returns True if execution can proceed immediately.
        Returns False if the pipeline must be halted for confirmation or denial.
        """
        pass
