import pytest
from edith.memory.memory_manager import MemoryManager
from edith.memory.memory_repository import MemoryRepository
from edith.memory.providers.sqlite_provider import SqliteProvider
from edith.memory.providers.embedding_provider import DummyEmbeddingProvider
from edith.memory.memory_constants import MemoryCategory

@pytest.fixture
def manager():
    sqlite = SqliteProvider(":memory:")
    embeddings = DummyEmbeddingProvider()
    repo = MemoryRepository(sqlite, embeddings)
    return MemoryManager(repo)

def test_remember_explicit(manager):
    mem = manager.remember("Remember that my favorite color is blue.")
    assert mem is not None
    assert mem.category == MemoryCategory.PREFERENCE
    
    # Retrieval
    results = manager.recall("favorite color")
    assert len(results) > 0
    assert "blue" in results[0].value.lower()

def test_memory_consolidation(manager):
    # First memory
    manager.remember("Remember that my favorite IDE is VS Code.")
    
    # User changes preference
    manager.remember("Remember that my favorite IDE is Cursor.")
    
    results = manager.recall("favorite IDE")
    assert len(results) == 1
    
    mem = results[0]
    assert "Cursor" in mem.value
    assert "historical_values" in mem.metadata
    assert "VS Code" in mem.metadata["historical_values"][0]["value"]
