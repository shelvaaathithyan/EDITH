"""
Region Capture utilities.
"""

from typing import Tuple
from edith.capabilities.vision.capture_engine import CaptureEngine

class RegionCapture:
    def __init__(self, capture_engine: CaptureEngine):
        self.capture_engine = capture_engine

    def capture_bbox(self, x: int, y: int, width: int, height: int) -> str:
        """Captures a specific bounding box on screen."""
        return self.capture_engine.capture_region((x, y, width, height))
