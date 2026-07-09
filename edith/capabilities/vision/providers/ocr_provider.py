"""
Interfaces for OCR Providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class IOCRProvider(ABC):
    @abstractmethod
    def extract_text(self, image_path: str) -> str:
        """Extracts plain text from the image."""
        pass
        
    @abstractmethod
    def extract_with_boxes(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text along with bounding boxes and confidence scores.
        Returns a list of dicts: {'text': str, 'bbox': (x, y, w, h), 'confidence': float}
        """
        pass
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the OCR provider."""
        pass
