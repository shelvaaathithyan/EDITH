import pytest
from edith.memory.providers.sqlite_provider import SqliteProvider
from edith.memory.memory_models import Memory, MemoryCategory, MemorySource
from edith.memory.memory_exceptions import MemoryNotFoundError
from datetime import datetime

@pytest.fixture
def sqlite_provider():
    # Use in-memory DB for tests
    provider = SqliteProvider(":memory:")
    provider.initialize()
    return provider

def test_sqlite_crud(sqlite_provider):
    mem = Memory(
        category=MemoryCategory.FACT,
        title="Test Fact",
        value="This is a test fact.",
        source=MemorySource.EXPLICIT,
        tags=["test"]
    )
    
    # Create
    sqlite_provider.save_memory(mem)
    
    # Read
    fetched = sqlite_provider.get_memory(mem.id)
    assert fetched is not None
    assert fetched.title == "Test Fact"
    assert fetched.value == "This is a test fact."
    assert "test" in fetched.tags
    
    # Update
    fetched.value = "Updated fact."
    sqlite_provider.save_memory(fetched)
    
    updated = sqlite_provider.get_memory(mem.id)
    assert updated.value == "Updated fact."
    
    # Delete
    sqlite_provider.delete_memory(mem.id)
    assert sqlite_provider.get_memory(mem.id) is None

def test_list_by_category(sqlite_provider):
    m1 = Memory(category=MemoryCategory.FACT, title="F1", value="v1")
    m2 = Memory(category=MemoryCategory.PREFERENCE, title="P1", value="v2")
    m3 = Memory(category=MemoryCategory.FACT, title="F2", value="v3")
    
    sqlite_provider.save_memory(m1)
    sqlite_provider.save_memory(m2)
    sqlite_provider.save_memory(m3)
    
    facts = sqlite_provider.list_memories(MemoryCategory.FACT)
    assert len(facts) == 2
    
    prefs = sqlite_provider.list_memories(MemoryCategory.PREFERENCE)
    assert len(prefs) == 1
    
    all_mems = sqlite_provider.list_memories()
    assert len(all_mems) == 3
