import pytest
from datetime import datetime
from memory_store import SharedMemory, MemoryEntry

def test_memory_store_initialization():
    """Test memory store initialization."""
    memory = SharedMemory("sqlite")
    assert memory is not None

def test_store_and_retrieve():
    """Test storing and retrieving memory entries."""
    memory = SharedMemory("sqlite")
    
    # Create test entry
    entry = MemoryEntry(
        source="test_agent",
        type="test_type",
        timestamp=datetime.now(),
        extracted_values={"test": "value"}
    )
    
    # Store entry
    entry_id = memory.store(entry)
    assert entry_id is not None
    
    # Retrieve entry
    retrieved = memory.retrieve(entry_id)
    assert retrieved is not None
    assert retrieved.source == "test_agent"
    assert retrieved.type == "test_type"
    assert retrieved.extracted_values["test"] == "value"

def test_search():
    """Test searching memory entries."""
    memory = SharedMemory("sqlite")
    
    # Create and store test entries
    entry1 = MemoryEntry(
        source="agent1",
        type="type1",
        timestamp=datetime.now(),
        extracted_values={"key": "value1"}
    )
    entry2 = MemoryEntry(
        source="agent2",
        type="type2",
        timestamp=datetime.now(),
        extracted_values={"key": "value2"}
    )
    
    memory.store(entry1)
    memory.store(entry2)
    
    # Search by source
    results = memory.search(source="agent1")
    assert len(results) == 1
    assert results[0].source == "agent1"
    
    # Search by type
    results = memory.search(type="type2")
    assert len(results) == 1
    assert results[0].type == "type2" 