"""
EasyOCR Provider Implementation.
"""

from typing import List, Dict, Any
import logging
from edith.capabilities.vision.providers.ocr_provider import IOCRProvider
from edith.capabilities.vision.vision_exceptions import OCRError
from edith.utils.logger import logger

class EasyOCRProvider(IOCRProvider):
    def __init__(self, languages: List[str] = ['en']):
        self.languages = languages
        self._reader = None
        self._initialized = False

    def _initialize(self):
        if not self._initialized:
            try:
                import easyocr
                # Disable verbose easyocr logging
                logging.getLogger('easyocr').setLevel(logging.ERROR)
                self._reader = easyocr.Reader(self.languages, gpu=True) # Will fallback to CPU if no GPU
                self._initialized = True
            except ImportError:
                raise OCRError("EasyOCR is not installed. Please install it with 'pip install easyocr'.")
            except Exception as e:
                raise OCRError(f"Failed to initialize EasyOCR: {e}")

    @property
    def name(self) -> str:
        return "EasyOCR"

    def extract_text(self, image_path: str) -> str:
        self._initialize()
        try:
            results = self._reader.readtext(image_path, detail=0)
            return "\n".join(results)
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            raise OCRError(f"EasyOCR extraction failed: {e}")

    def extract_with_boxes(self, image_path: str) -> List[Dict[str, Any]]:
        self._initialize()
        try:
            # detail=1 returns (bbox, text, prob)
            results = self._reader.readtext(image_path, detail=1)
            formatted = []
            for bbox, text, prob in results:
                # bbox is a list of 4 points: [tl, tr, br, bl]
                tl = bbox[0]
                br = bbox[2]
                x = int(tl[0])
                y = int(tl[1])
                w = int(br[0] - tl[0])
                h = int(br[1] - tl[1])
                
                formatted.append({
                    'text': text,
                    'bbox': (x, y, w, h),
                    'confidence': float(prob)
                })
            return formatted
        except Exception as e:
            logger.error(f"EasyOCR bounding box extraction failed: {e}")
            raise OCRError(f"EasyOCR bounding box extraction failed: {e}")
