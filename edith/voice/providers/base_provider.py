from abc import ABC, abstractmethod

class BaseTTSProvider(ABC):
    @abstractmethod
    def initialize(self):
        """Initializes the TTS provider (downloads models, loads them, etc.)"""
        pass

    @abstractmethod
    def speak(self, text: str, interruptible: bool = True):
        """Synthesizes text and plays it. Blocks until finished unless interrupted."""
        pass

    @abstractmethod
    def interrupt(self):
        """Stops the current playback immediately."""
        pass

    @abstractmethod
    def stop(self):
        """Stops the provider and cleans up resources."""
        pass
