"""
OCR Engine. Wraps the OCR Provider and abstracts text extraction.
"""

from typing import List, Dict, Any, Tuple
from edith.capabilities.vision.providers.ocr_provider import IOCRProvider
from edith.capabilities.vision.vision_exceptions import OCRError

class OCREngine:
    def __init__(self, provider: IOCRProvider):
        self.provider = provider

    def extract_text(self, image_path: str) -> str:
        """Extracts plain text from the image."""
        try:
            return self.provider.extract_text(image_path)
        except Exception as e:
            raise OCRError(f"OCR text extraction failed: {e}")

    def extract_with_boxes(self, image_path: str) -> List[Dict[str, Any]]:
        """Extracts text with bounding boxes."""
        try:
            return self.provider.extract_with_boxes(image_path)
        except Exception as e:
            raise OCRError(f"OCR bounding box extraction failed: {e}")
