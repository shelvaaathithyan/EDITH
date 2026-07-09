"""
Manifest definition for the Vision Perception Engine Capability.
"""

from edith.sdk.capability.capability_models import CapabilityManifest
from edith.permission.permission_models import RiskLevel
from edith.capabilities.vision.vision_constants import VisionAction

def get_vision_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id="core.vision",
        name="Vision Perception Engine",
        version="1.0.0",
        author="EDITH Core",
        description="Grants EDITH the ability to see and analyze the desktop, windows, and images via OCR and Multimodal LLMs.",
        supported_platforms=["windows", "macos", "linux"],
        dependencies=[],  # No hard capability dependencies, but relies on Ollama/MSS
        supported_actions=[
            VisionAction.CAPTURE_SCREEN,
            VisionAction.CAPTURE_WINDOW,
            VisionAction.CAPTURE_REGION,
            VisionAction.CAPTURE_CLIPBOARD,
            VisionAction.ANALYZE_IMAGE,
            VisionAction.ANALYZE_SCREEN,
            VisionAction.EXTRACT_TEXT,
            VisionAction.SUMMARIZE_DOCUMENT,
            VisionAction.ANSWER_QUESTION,
            VisionAction.READ_PDF
        ],
        risk_matrix={
            VisionAction.CAPTURE_SCREEN: RiskLevel.HIGH,        # Reading the whole screen
            VisionAction.CAPTURE_WINDOW: RiskLevel.MEDIUM,      # Target app might have PII
            VisionAction.CAPTURE_REGION: RiskLevel.MEDIUM,
            VisionAction.CAPTURE_CLIPBOARD: RiskLevel.CRITICAL, # Clipboard might contain passwords
            VisionAction.ANALYZE_IMAGE: RiskLevel.LOW,
            VisionAction.ANALYZE_SCREEN: RiskLevel.HIGH,
            VisionAction.EXTRACT_TEXT: RiskLevel.LOW,
            VisionAction.SUMMARIZE_DOCUMENT: RiskLevel.LOW,
            VisionAction.ANSWER_QUESTION: RiskLevel.LOW,
            VisionAction.READ_PDF: RiskLevel.MEDIUM           # PDFs could be sensitive
        }
    )
