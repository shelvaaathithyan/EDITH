"""
Window Capture utilities.
"""

from typing import Optional, Tuple
from edith.capabilities.vision.vision_exceptions import CaptureError
from edith.capabilities.vision.vision_models import WindowInfo, BoundingBox

class WindowCapture:
    def __init__(self, capture_engine):
        self.capture_engine = capture_engine
        self._initialized = False

    def _initialize(self):
        if not self._initialized:
            try:
                import pygetwindow as gw
                self.gw = gw
                self._initialized = True
            except ImportError:
                raise CaptureError("pygetwindow is not installed. Please install it with 'pip install pygetwindow'.")
            except Exception as e:
                raise CaptureError(f"Failed to initialize pygetwindow: {e}")

    def get_active_window(self) -> WindowInfo:
        self._initialize()
        try:
            win = self.gw.getActiveWindow()
            if not win:
                raise CaptureError("No active window found.")
            
            bbox = BoundingBox(x=win.left, y=win.top, width=win.width, height=win.height)
            # In a real implementation, we'd use psutil to get PID, but pygetwindow lacks it.
            # We'll mock process/pid for now.
            return WindowInfo(
                title=win.title,
                process="unknown",
                pid=0,
                bbox=bbox,
                is_active=True
            )
        except Exception as e:
            raise CaptureError(f"Failed to get active window info: {e}")

    def capture_active_window(self) -> str:
        """Finds the active window boundaries and captures that region."""
        win_info = self.get_active_window()
        bbox_tuple = (win_info.bbox.x, win_info.bbox.y, win_info.bbox.width, win_info.bbox.height)
        return self.capture_engine.capture_region(bbox_tuple)
