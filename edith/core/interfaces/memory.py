from abc import ABC, abstractmethod

class IMemoryManager(ABC):
    @abstractmethod
    def store(self, role: str, content: str) -> None:
        pass

    @abstractmethod
    def get_history(self) -> str:
        pass
