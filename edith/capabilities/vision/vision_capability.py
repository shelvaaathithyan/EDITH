"""
Vision Capability Root.
"""

import threading
from typing import Dict, Any

from edith.sdk.capability.base_capability import BaseCapability
from edith.sdk.capability.capability_models import CapabilityManifest, CapabilityResult
from edith.core.events import event_bus, AppEvent

from edith.capabilities.vision.vision_manifest import get_vision_manifest
from edith.capabilities.vision.vision_constants import VisionAction
from edith.capabilities.vision.vision_exceptions import VisionException
from edith.capabilities.vision.vision_events import VisionEvents

from edith.capabilities.vision.vision_controller import VisionController
from edith.capabilities.vision.providers.ollama_vision_provider import OllamaVisionProvider
from edith.capabilities.vision.providers.easyocr_provider import EasyOCRProvider

class VisionCapability(BaseCapability):
    def __init__(self):
        super().__init__()
        # Use default providers as requested
        vision_provider = OllamaVisionProvider(model="qwen2.5-vl")
        ocr_provider = EasyOCRProvider()
        self.controller = VisionController(vision_provider, ocr_provider)

    def get_manifest(self) -> CapabilityManifest:
        return get_vision_manifest()

    def _do_initialize(self) -> None:
        """Initializes vision models and resources."""
        # Register capability actions
        self.register_action(VisionAction.CAPTURE_SCREEN, self.capture_screen)
        self.register_action(VisionAction.ANALYZE_SCREEN, self.analyze_screen)
        self.register_action(VisionAction.EXTRACT_TEXT, self.extract_text)
        self.register_action(VisionAction.CAPTURE_WINDOW, self.capture_window)
        # etc...

    def capture_screen(self, args: Dict[str, Any]) -> CapabilityResult:
        # Just capturing, no analysis yet
        path = self.controller.capture_engine.capture_desktop()
        return CapabilityResult(success=True, data={"image_path": path})

    def analyze_screen(self, args: Dict[str, Any]) -> CapabilityResult:
        prompt = args.get("prompt", "Analyze this screen.")
        res = self.controller.capture_and_analyze_screen(prompt)
        return CapabilityResult(success=True, data=res.model_dump())

    def extract_text(self, args: Dict[str, Any]) -> CapabilityResult:
        path = args.get("image_path")
        if not path:
            return CapabilityResult(success=False, error="image_path required")
        text = self.controller.ocr_engine.extract_text(path)
        return CapabilityResult(success=True, data={"text": text})
        
    def capture_window(self, args: Dict[str, Any]) -> CapabilityResult:
        from edith.capabilities.vision.window_capture import WindowCapture
        wc = WindowCapture(self.controller.capture_engine)
        path = wc.capture_active_window()
        return CapabilityResult(success=True, data={"image_path": path})
