from abc import ABC, abstractmethod
from edith.ai.models import ExecutionPlan

class IPermissionManager(ABC):
    @abstractmethod
    def request_permission(self, plan: ExecutionPlan) -> bool:
        """Returns True if permission is granted, False otherwise."""
        pass
