"""
Clipboard Capture.
"""

from typing import Optional
from PIL import Image, ImageGrab
import os
import tempfile
import uuid
from edith.capabilities.vision.vision_exceptions import CaptureError

class ClipboardCapture:
    def __init__(self):
        self._temp_dir = tempfile.gettempdir()

    def capture_clipboard(self) -> Optional[str]:
        """Reads image from clipboard. Returns filepath or None if no image."""
        try:
            img = ImageGrab.grabclipboard()
            if img is None:
                return None
                
            if isinstance(img, list):
                # Sometimes it returns a list of files if files were copied, not pixel data
                # We could try to read the first file if it's an image.
                img_path = img[0]
                if not os.path.exists(img_path):
                    return None
                return img_path
                
            if isinstance(img, Image.Image):
                filepath = os.path.join(self._temp_dir, f"edith_clipboard_{uuid.uuid4().hex[:8]}.png")
                # Handle images with alpha channel before saving as JPEG/PNG
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new(img.mode[:-1], img.size, (255, 255, 255))
                    background.paste(img, img.split()[-1])
                    img = background
                
                img.save(filepath, format="PNG")
                return filepath
                
            return None
        except Exception as e:
            raise CaptureError(f"Failed to capture clipboard: {e}")
