"""
UI Detector. 
Analyzes OCR results or image boundaries to identify UI elements.
"""

from typing import List, Dict, Any
from edith.capabilities.vision.vision_models import UIElement, BoundingBox

class UIDetector:
    def __init__(self):
        pass

    def detect_from_ocr(self, ocr_results: List[Dict[str, Any]]) -> List[UIElement]:
        """
        Heuristic-based UI detection using OCR bounding boxes.
        In a full implementation, this could use a YOLO model or OpenCV contour detection.
        For now, we will create rudimentary elements based on text shapes.
        """
        elements = []
        for res in ocr_results:
            text = res['text']
            bbox_raw = res['bbox']
            conf = res['confidence']
            
            # Simple heuristic: if text is short and title cased, might be a button or label
            ui_type = "TextLabel"
            if len(text) < 15 and text.istitle():
                ui_type = "Button"
                
            bbox = BoundingBox(x=bbox_raw[0], y=bbox_raw[1], width=bbox_raw[2], height=bbox_raw[3])
            
            elements.append(UIElement(
                type=ui_type,
                text=text,
                bbox=bbox,
                confidence=conf
            ))
            
        return elements
