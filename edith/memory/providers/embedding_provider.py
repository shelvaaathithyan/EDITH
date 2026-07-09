"""
Embedding Provider interface and dummy implementation.
"""

from abc import ABC, abstractmethod
from typing import List

class IEmbeddingProvider(ABC):
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generates a semantic vector embedding for the given text."""
        pass
        
    @abstractmethod
    def store_embedding(self, memory_id: str, embedding: List[float]) -> str:
        """Stores the embedding and returns the embedding_id."""
        pass
        
    @abstractmethod
    def search_embedding(self, embedding: List[float], limit: int = 10) -> List[str]:
        """Searches for similar embeddings, returning a list of memory_ids."""
        pass
        
    @abstractmethod
    def delete_embedding(self, embedding_id: str) -> None:
        """Deletes an embedding."""
        pass

class DummyEmbeddingProvider(IEmbeddingProvider):
    """
    A stubbed embedding provider for future ML model integration.
    """
    def generate_embedding(self, text: str) -> List[float]:
        return [0.0] * 128  # Dummy vector
        
    def store_embedding(self, memory_id: str, embedding: List[float]) -> str:
        # Currently no-op
        return f"emb_{memory_id}"
        
    def search_embedding(self, embedding: List[float], limit: int = 10) -> List[str]:
        return []
        
    def delete_embedding(self, embedding_id: str) -> None:
        pass
