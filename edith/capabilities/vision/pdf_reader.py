"""
PDF Reader capability for the Vision Perception Engine.
Extracts text and renders pages to images for vision processing.
"""

import os
import tempfile
import uuid
from typing import List, Dict, Any
from PIL import Image
from edith.capabilities.vision.vision_exceptions import VisionException
from edith.utils.logger import logger

class PDFReader:
    def __init__(self):
        self._temp_dir = tempfile.gettempdir()
        self._initialized = False

    def _initialize(self):
        if not self._initialized:
            try:
                import fitz  # PyMuPDF
                self.fitz = fitz
                self._initialized = True
            except ImportError:
                raise VisionException("PyMuPDF is not installed. Please install it with 'pip install pymupdf'.")
            except Exception as e:
                raise VisionException(f"Failed to initialize PyMuPDF: {e}")

    def extract_text(self, pdf_path: str) -> str:
        """Extracts plain text directly from the PDF."""
        self._initialize()
        try:
            doc = self.fitz.open(pdf_path)
            full_text = []
            for page in doc:
                full_text.append(page.get_text())
            return "\n\n".join(full_text)
        except Exception as e:
            raise VisionException(f"Failed to read PDF text: {e}")

    def render_page(self, pdf_path: str, page_number: int = 0) -> str:
        """Renders a specific page to an image and returns the file path."""
        self._initialize()
        try:
            doc = self.fitz.open(pdf_path)
            if page_number < 0 or page_number >= len(doc):
                raise ValueError(f"Invalid page number {page_number}")
                
            page = doc.load_page(page_number)
            pix = page.get_pixmap(dpi=150)
            
            img_path = os.path.join(self._temp_dir, f"edith_pdf_{uuid.uuid4().hex[:8]}.png")
            pix.save(img_path)
            
            return img_path
        except Exception as e:
            raise VisionException(f"Failed to render PDF page: {e}")
