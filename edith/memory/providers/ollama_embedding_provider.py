"""
Ollama Embedding Provider.
Uses Ollama's /api/embeddings endpoint for real semantic vector generation.
"""

import json
import urllib.request
import urllib.error
from typing import List
from edith.memory.providers.embedding_provider import IEmbeddingProvider
from edith.utils.logger import get_logger

logger = get_logger("edith.memory.embedding")


class OllamaEmbeddingProvider(IEmbeddingProvider):
    """
    Production embedding provider using Ollama's local API.
    Default model: nomic-embed-text (768 dimensions).
    """

    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self._embedding_store: dict[str, List[float]] = {}

    def generate_embedding(self, text: str) -> List[float]:
        """Generates a semantic vector embedding for the given text via Ollama."""
        try:
            payload = json.dumps({"model": self.model, "prompt": text}).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/embeddings",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                embedding = result.get("embedding", [])
                if not embedding:
                    logger.warning(f"Ollama returned empty embedding for model={self.model}")
                    return []
                return embedding
        except urllib.error.URLError as e:
            logger.error(f"Ollama embedding request failed (is Ollama running?): {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {e}")
            return []

    def store_embedding(self, memory_id: str, embedding: List[float]) -> str:
        """Stores the embedding in-memory, keyed by memory_id."""
        emb_id = f"emb_{memory_id}"
        self._embedding_store[emb_id] = embedding
        return emb_id

    def search_embedding(self, embedding: List[float], limit: int = 10) -> List[str]:
        """
        Performs cosine similarity search against stored embeddings.
        Returns memory_ids sorted by relevance.
        """
        if not embedding or not self._embedding_store:
            return []

        scores: list[tuple[str, float]] = []
        for emb_id, stored_vec in self._embedding_store.items():
            if len(stored_vec) != len(embedding):
                continue
            sim = self._cosine_similarity(embedding, stored_vec)
            # Extract memory_id from emb_id (strip "emb_" prefix)
            memory_id = emb_id[4:] if emb_id.startswith("emb_") else emb_id
            scores.append((memory_id, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [mid for mid, _ in scores[:limit]]

    def delete_embedding(self, embedding_id: str) -> None:
        """Removes an embedding from the store."""
        self._embedding_store.pop(embedding_id, None)

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Computes cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
