from abc import ABC, abstractmethod
from typing import Dict, Any

class IContextManager(ABC):
    @abstractmethod
    def update_context(self, context_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_context(self) -> Dict[str, Any]:
        pass
