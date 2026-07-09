from abc import ABC, abstractmethod

class IResponseGenerator(ABC):
    @abstractmethod
    def generate(self, context: any) -> str:
        """Takes an orchestration context or execution result and generates text for the VoiceManager."""
        pass
