"""
Capture Engine. Handles desktop/monitor screenshots using mss.
"""

from typing import Optional, Tuple
import os
import tempfile
from PIL import Image
from edith.capabilities.vision.vision_exceptions import CaptureError

class CaptureEngine:
    def __init__(self):
        self._temp_dir = tempfile.gettempdir()
        self._initialized = False

    def _initialize(self):
        if not self._initialized:
            try:
                import mss
                self.mss = mss.mss()
                self._initialized = True
            except ImportError:
                raise CaptureError("mss is not installed. Please install it with 'pip install mss'.")
            except Exception as e:
                raise CaptureError(f"Failed to initialize mss: {e}")

    def _save_temp_image(self, img: Image.Image, prefix: str = "capture_") -> str:
        import uuid
        filepath = os.path.join(self._temp_dir, f"edith_{prefix}{uuid.uuid4().hex[:8]}.png")
        img.save(filepath, format="PNG")
        return filepath

    def capture_desktop(self, monitor_index: int = 0) -> str:
        """
        Captures the entire desktop or a specific monitor.
        monitor_index=0 captures all monitors merged.
        monitor_index=1 captures the primary monitor.
        """
        self._initialize()
        try:
            # mss monitors: 0 is all monitors combined, 1 is primary, 2 is secondary, etc.
            monitor = self.mss.monitors[monitor_index]
            sct_img = self.mss.grab(monitor)
            
            # Convert mss ScreenShot to PIL Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return self._save_temp_image(img, "desktop_")
        except Exception as e:
            raise CaptureError(f"Desktop capture failed: {e}")

    def capture_region(self, bbox: Tuple[int, int, int, int]) -> str:
        """
        Captures a specific region (x, y, width, height).
        """
        self._initialize()
        try:
            x, y, w, h = bbox
            region = {"top": y, "left": x, "width": w, "height": h}
            sct_img = self.mss.grab(region)
            
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return self._save_temp_image(img, "region_")
        except Exception as e:
            raise CaptureError(f"Region capture failed: {e}")
