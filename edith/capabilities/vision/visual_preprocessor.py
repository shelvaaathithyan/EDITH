"""
Visual Preprocessor.
Normalizes, resizes, crops, and improves contrast for captured images before OCR/Vision.
"""

from PIL import Image, ImageEnhance
import os
import tempfile
import uuid
from typing import Tuple
from edith.capabilities.vision.vision_exceptions import CaptureError
from edith.utils.logger import logger

class VisualPreprocessor:
    def __init__(self):
        self._temp_dir = tempfile.gettempdir()

    def _save_temp_image(self, img: Image.Image, prefix: str = "prep_") -> str:
        filepath = os.path.join(self._temp_dir, f"edith_{prefix}{uuid.uuid4().hex[:8]}.png")
        img.save(filepath, format="PNG")
        return filepath

    def preprocess(self, image_path: str, max_size: int = 1920) -> str:
        """
        Runs standard preprocessing pipeline:
        1. Resize if too large
        2. Enhance contrast
        """
        try:
            img = Image.open(image_path)
            
            # Resize
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
            # Enhance Contrast slightly for better OCR
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
            
            return self._save_temp_image(img)
            
        except Exception as e:
            logger.error(f"Failed to preprocess image: {e}")
            # Fallback to original image
            return image_path
