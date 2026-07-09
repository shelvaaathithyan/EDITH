"""
Models for the Vision Perception Engine.
"""

from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

class UIElement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # Button, Textbox, Checkbox, Dialog, etc.
    text: Optional[str] = None
    bbox: BoundingBox
    confidence: float

class WindowInfo(BaseModel):
    title: str
    process: str
    pid: int
    bbox: BoundingBox
    is_active: bool

class ImageAnalysisResult(BaseModel):
    summary: str
    detected_text: str
    detected_ui_elements: List[UIElement] = Field(default_factory=list)
    detected_windows: List[WindowInfo] = Field(default_factory=list)
    detected_errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    latency: float

class VisionSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = Field(default_factory=datetime.now)
    frames: List[ImageAnalysisResult] = Field(default_factory=list)
