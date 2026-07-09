"""
Ollama Vision Provider implementation.
Supports configurable models like qwen2.5-vl, llama3.2-vision, and llava.
"""

import base64
import requests
import json
from typing import Dict, Any

from edith.capabilities.vision.providers.vision_provider import IVisionProvider
from edith.capabilities.vision.vision_exceptions import VisionProviderError
from edith.utils.logger import logger

class OllamaVisionProvider(IVisionProvider):
    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen2.5-vl"):
        self.host = host
        self._model = model
        
    @property
    def model_name(self) -> str:
        return self._model
        
    def _encode_image(self, image_path: str) -> str:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise VisionProviderError(f"Failed to encode image {image_path}: {e}")

    def _generate(self, prompt: str, image_path: str) -> str:
        """Helper to call Ollama generate API with an image."""
        url = f"{self.host}/api/generate"
        b64_image = self._encode_image(image_path)
        
        payload = {
            "model": self._model,
            "prompt": prompt,
            "images": [b64_image],
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except requests.RequestException as e:
            logger.error(f"Ollama Vision API error: {e}")
            raise VisionProviderError(f"Ollama Vision API error: {e}")

    def analyze_image(self, image_path: str, prompt: str) -> str:
        full_prompt = f"Analyze this image. {prompt}"
        return self._generate(full_prompt, image_path)

    def analyze_screen(self, image_path: str, prompt: str) -> str:
        full_prompt = f"This is a screenshot of a user's desktop. {prompt}"
        return self._generate(full_prompt, image_path)

    def summarize_document(self, image_path: str) -> str:
        return self._generate("Summarize the contents of this document.", image_path)

    def answer_question(self, image_path: str, question: str) -> str:
        return self._generate(f"Answer the following question based on the image: {question}", image_path)
