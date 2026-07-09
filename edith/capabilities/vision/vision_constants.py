"""
Constants for the Vision Perception Engine.
"""

from enum import Enum

class VisionAction(str, Enum):
    CAPTURE_SCREEN = "capture_screen"
    CAPTURE_WINDOW = "capture_window"
    CAPTURE_REGION = "capture_region"
    CAPTURE_CLIPBOARD = "capture_clipboard"
    ANALYZE_IMAGE = "analyze_image"
    ANALYZE_SCREEN = "analyze_screen"
    EXTRACT_TEXT = "extract_text"
    SUMMARIZE_DOCUMENT = "summarize_document"
    ANSWER_QUESTION = "answer_question"
    READ_PDF = "read_pdf"

class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
