"""
Long-Term Memory Subsystem.
"""

from edith.memory.memory_manager import MemoryManager
from edith.memory.memory_repository import MemoryRepository
from edith.memory.providers.sqlite_provider import SqliteProvider
from edith.memory.providers.ollama_embedding_provider import OllamaEmbeddingProvider
from edith.memory.memory_constants import MemoryCategory, MemorySource
from edith.config.settings import settings


def get_memory_manager(db_path: str = "edith_ltm.db") -> MemoryManager:
    sqlite_provider = SqliteProvider(db_path)
    embedding_provider = OllamaEmbeddingProvider(
        model=settings.embedding_model
    )
    repo = MemoryRepository(sqlite_provider, embedding_provider)
    return MemoryManager(repo)


# Expose a default singleton for ease of use across the app
memory_manager = get_memory_manager()
