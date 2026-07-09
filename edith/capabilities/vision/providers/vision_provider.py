"""
Interfaces for Vision Providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class IVisionProvider(ABC):
    @abstractmethod
    def analyze_image(self, image_path: str, prompt: str) -> str:
        """Analyzes an image and returns a text response."""
        pass
        
    @abstractmethod
    def analyze_screen(self, image_path: str, prompt: str) -> str:
        """Analyzes a full screen screenshot."""
        pass
        
    @abstractmethod
    def summarize_document(self, image_path: str) -> str:
        """Summarizes a document image."""
        pass
        
    @abstractmethod
    def answer_question(self, image_path: str, question: str) -> str:
        """Answers a specific question about the image."""
        pass
        
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the name of the underlying model."""
        pass
