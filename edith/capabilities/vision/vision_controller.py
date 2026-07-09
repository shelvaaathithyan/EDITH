"""
Vision Controller. Orchestrates the Perception Pipeline.
"""

from typing import Dict, Any, List, Optional
import time
from concurrent.futures import ThreadPoolExecutor

from edith.capabilities.vision.vision_models import ImageAnalysisResult, VisionSession
from edith.capabilities.vision.capture_engine import CaptureEngine
from edith.capabilities.vision.visual_preprocessor import VisualPreprocessor
from edith.capabilities.vision.ocr_engine import OCREngine
from edith.capabilities.vision.ui_detector import UIDetector
from edith.capabilities.vision.image_analyzer import ScreenAnalyzer, ImageAnalyzer
from edith.capabilities.vision.pdf_reader import PDFReader
from edith.capabilities.vision.providers.vision_provider import IVisionProvider
from edith.capabilities.vision.providers.ocr_provider import IOCRProvider
from edith.capabilities.vision.vision_events import VisionEvents
from edith.core.events import event_bus, AppEvent

class VisionController:
    def __init__(self, vision_provider: IVisionProvider, ocr_provider: IOCRProvider):
        self.vision_provider = vision_provider
        self.ocr_provider = ocr_provider
        
        self.capture_engine = CaptureEngine()
        self.preprocessor = VisualPreprocessor()
        self.ocr_engine = OCREngine(self.ocr_provider)
        self.ui_detector = UIDetector()
        self.screen_analyzer = ScreenAnalyzer(self.vision_provider)
        self.image_analyzer = ImageAnalyzer(self.vision_provider)
        self.pdf_reader = PDFReader()
        
        self.active_session: Optional[VisionSession] = None
        self.executor = ThreadPoolExecutor(max_workers=2)

    def start_session(self) -> VisionSession:
        self.active_session = VisionSession()
        return self.active_session

    def process_pipeline(self, image_path: str, prompt: str, is_screen: bool = True) -> ImageAnalysisResult:
        """Executes the full perception pipeline."""
        start_time = time.time()
        
        # 1. Preprocess
        prep_path = self.preprocessor.preprocess(image_path)
        
        # 2. OCR
        ocr_boxes = self.ocr_engine.extract_with_boxes(prep_path)
        ocr_text = "\n".join([b['text'] for b in ocr_boxes])
        
        event_bus.publish(AppEvent.OCR_COMPLETED, {"text": ocr_text})
        
        # 3. UI Detection
        ui_elements = self.ui_detector.detect_from_ocr(ocr_boxes)
        if ui_elements:
            event_bus.publish(AppEvent.UI_DETECTED, {"count": len(ui_elements)})
            
        # 4. Vision Provider
        if is_screen:
            summary = self.screen_analyzer.analyze(prep_path, ocr_text, ui_elements, prompt)
        else:
            summary = self.image_analyzer.analyze(prep_path, prompt)
            
        latency = time.time() - start_time
        
        result = ImageAnalysisResult(
            summary=summary,
            detected_text=ocr_text,
            detected_ui_elements=ui_elements,
            detected_windows=[], # Populated via window_capture if requested
            latency=latency
        )
        
        if self.active_session:
            self.active_session.frames.append(result)
            
        event_bus.publish(AppEvent.VISION_ANALYZED, result.model_dump())
        return result
        
    def capture_and_analyze_screen(self, prompt: str = "Analyze this screen") -> ImageAnalysisResult:
        # Offload capture
        img_path = self.capture_engine.capture_desktop()
        event_bus.publish(AppEvent.SCREEN_CAPTURED, {"path": img_path})
        
        return self.process_pipeline(img_path, prompt, is_screen=True)
