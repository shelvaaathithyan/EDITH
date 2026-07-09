"""
Image and Screen Analyzers.
"""

from typing import Dict, Any, List
from edith.capabilities.vision.providers.vision_provider import IVisionProvider
from edith.capabilities.vision.vision_models import UIElement, WindowInfo

class ImageAnalyzer:
    def __init__(self, provider: IVisionProvider):
        self.provider = provider

    def analyze(self, image_path: str, prompt: str = "Describe this image in detail.") -> str:
        return self.provider.analyze_image(image_path, prompt)

class ScreenAnalyzer:
    def __init__(self, provider: IVisionProvider):
        self.provider = provider

    def analyze(self, image_path: str, ocr_text: str, ui_elements: List[UIElement], prompt: str = "Describe the current state of my screen.") -> str:
        """Analyzes a screen utilizing OCR and UI data as additional prompt context."""
        
        enriched_prompt = f"{prompt}\n\n"
        if ocr_text:
            enriched_prompt += f"Extracted Text:\n{ocr_text[:2000]}...\n\n"
            
        if ui_elements:
            ui_desc = ", ".join([f"{el.type}('{el.text}')" for el in ui_elements[:15]])
            enriched_prompt += f"Detected UI Elements: {ui_desc}\n\n"
            
        return self.provider.analyze_screen(image_path, enriched_prompt)
