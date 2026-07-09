import pytest
from unittest.mock import MagicMock, patch
from edith.capabilities.vision.vision_controller import VisionController
from edith.capabilities.vision.providers.vision_provider import IVisionProvider
from edith.capabilities.vision.providers.ocr_provider import IOCRProvider
from edith.capabilities.vision.vision_models import ImageAnalysisResult

class MockVisionProvider(IVisionProvider):
    @property
    def model_name(self) -> str:
        return "mock-model"
    def analyze_image(self, p, pr) -> str: return "Mock image analysis"
    def analyze_screen(self, p, pr) -> str: return "Mock screen analysis"
    def summarize_document(self, p) -> str: return "Mock doc summary"
    def answer_question(self, p, q) -> str: return "Mock answer"

class MockOCRProvider(IOCRProvider):
    @property
    def name(self) -> str: return "mock-ocr"
    def extract_text(self, p) -> str: return "Mock Text"
    def extract_with_boxes(self, p): return [{"text": "Login", "bbox": (0,0,10,10), "confidence": 0.99}]

@pytest.fixture
def controller():
    vision = MockVisionProvider()
    ocr = MockOCRProvider()
    ctrl = VisionController(vision, ocr)
    
    # Mock file-system specific components to avoid real Pillow/File IO
    ctrl.preprocessor.preprocess = MagicMock(return_value="mock_path.png")
    ctrl.capture_engine.capture_desktop = MagicMock(return_value="mock_screenshot.png")
    return ctrl

def test_process_pipeline(controller):
    res = controller.process_pipeline("dummy.png", "Test prompt", is_screen=True)
    
    assert isinstance(res, ImageAnalysisResult)
    assert res.detected_text == "Login"
    assert len(res.detected_ui_elements) == 1
    assert res.detected_ui_elements[0].text == "Login"
    assert res.summary == "Mock screen analysis"
    assert controller.preprocessor.preprocess.called

def test_capture_and_analyze(controller):
    res = controller.capture_and_analyze_screen("Test")
    assert controller.capture_engine.capture_desktop.called
    assert res.summary == "Mock screen analysis"
