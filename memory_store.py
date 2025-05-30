from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import json
import sqlite3
import redis
from dataclasses import dataclass, asdict

@dataclass
class MemoryEntry:
    """Lightweight memory entry structure."""
    source: str
    type: str
    timestamp: datetime
    thread_id: Optional[str] = None
    conversation_id: Optional[str] = None
    extracted_values: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary format."""
        data = asdict(self)
        data['timestamp'] = data['timestamp'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create entry from dictionary format."""
        if 'timestamp' in data:
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class MemoryBackend(ABC):
    """Abstract base class for memory storage backends."""
    
    @abstractmethod
    def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry and return its ID."""
        pass
    
    @abstractmethod
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID."""
        pass
    
    @abstractmethod
    def search(self, 
              source: Optional[str] = None,
              type: Optional[str] = None,
              thread_id: Optional[str] = None,
              conversation_id: Optional[str] = None,
              start_time: Optional[datetime] = None,
              end_time: Optional[datetime] = None) -> List[MemoryEntry]:
        """Search for memory entries based on criteria."""
        pass

class SQLiteBackend(MemoryBackend):
    """SQLite-based memory storage backend."""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            # Check if the table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory_entries';")
            if not cursor.fetchone():
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS memory_entries (
                        id TEXT PRIMARY KEY,
                        source TEXT NOT NULL,
                        type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        thread_id TEXT,
                        conversation_id TEXT,
                        extracted_values TEXT
                    )
                """)
    
    def store(self, entry: MemoryEntry) -> str:
        """Store entry in SQLite."""
        entry_id = f"{entry.source}_{entry.timestamp.timestamp()}"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO memory_entries 
                (id, source, type, timestamp, thread_id, conversation_id, extracted_values)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id,
                entry.source,
                entry.type,
                entry.timestamp.isoformat(),
                entry.thread_id,
                entry.conversation_id,
                json.dumps(entry.extracted_values or {})
            ))
        return entry_id
    
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve entry from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM memory_entries WHERE id = ?",
                (entry_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            return MemoryEntry(
                source=row[1],
                type=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                thread_id=row[4],
                conversation_id=row[5],
                extracted_values=json.loads(row[6])
            )
    
    def search(self, **kwargs) -> List[MemoryEntry]:
        """Search entries in SQLite."""
        conditions = []
        params = []
        
        if kwargs.get('source'):
            conditions.append("source = ?")
            params.append(kwargs['source'])
        if kwargs.get('type'):
            conditions.append("type = ?")
            params.append(kwargs['type'])
        if kwargs.get('thread_id'):
            conditions.append("thread_id = ?")
            params.append(kwargs['thread_id'])
        if kwargs.get('conversation_id'):
            conditions.append("conversation_id = ?")
            params.append(kwargs['conversation_id'])
        if kwargs.get('start_time'):
            conditions.append("timestamp >= ?")
            params.append(kwargs['start_time'].isoformat())
        if kwargs.get('end_time'):
            conditions.append("timestamp <= ?")
            params.append(kwargs['end_time'].isoformat())
        
        query = "SELECT * FROM memory_entries"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return [
                MemoryEntry(
                    source=row[1],
                    type=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    thread_id=row[4],
                    conversation_id=row[5],
                    extracted_values=json.loads(row[6])
                )
                for row in cursor.fetchall()
            ]

class RedisBackend(MemoryBackend):
    """Redis-based memory storage backend."""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.redis = redis.Redis(host=host, port=port, db=db)
    
    def store(self, entry: MemoryEntry) -> str:
        """Store entry in Redis."""
        entry_id = f"{entry.source}_{entry.timestamp.timestamp()}"
        data = entry.to_dict()
        self.redis.hmset(f"memory:{entry_id}", data)
        return entry_id
    
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve entry from Redis."""
        data = self.redis.hgetall(f"memory:{entry_id}")
        if not data:
            return None
        return MemoryEntry.from_dict(data)
    
    def search(self, **kwargs) -> List[MemoryEntry]:
        """Search entries in Redis."""
        # Note: Redis doesn't support complex queries natively
        # This is a simplified implementation
        entries = []
        for key in self.redis.keys("memory:*"):
            entry = self.retrieve(key.decode().split(":")[1])
            if self._matches_criteria(entry, kwargs):
                entries.append(entry)
        return entries
    
    def _matches_criteria(self, entry: MemoryEntry, criteria: Dict) -> bool:
        """Check if entry matches search criteria."""
        if criteria.get('source') and entry.source != criteria['source']:
            return False
        if criteria.get('type') and entry.type != criteria['type']:
            return False
        if criteria.get('thread_id') and entry.thread_id != criteria['thread_id']:
            return False
        if criteria.get('conversation_id') and entry.conversation_id != criteria['conversation_id']:
            return False
        if criteria.get('start_time') and entry.timestamp < criteria['start_time']:
            return False
        if criteria.get('end_time') and entry.timestamp > criteria['end_time']:
            return False
        return True

class InMemoryBackend(MemoryBackend):
    """Simple in-memory storage backend."""
    
    def __init__(self):
        self.entries: Dict[str, MemoryEntry] = {}
    
    def store(self, entry: MemoryEntry) -> str:
        """Store entry in memory."""
        entry_id = f"{entry.source}_{entry.timestamp.timestamp()}"
        self.entries[entry_id] = entry
        return entry_id
    
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve entry from memory."""
        return self.entries.get(entry_id)
    
    def search(self, **kwargs) -> List[MemoryEntry]:
        """Search entries in memory."""
        return [
            entry for entry in self.entries.values()
            if self._matches_criteria(entry, kwargs)
        ]
    
    def _matches_criteria(self, entry: MemoryEntry, criteria: Dict) -> bool:
        """Check if entry matches search criteria."""
        if criteria.get('source') and entry.source != criteria['source']:
            return False
        if criteria.get('type') and entry.type != criteria['type']:
            return False
        if criteria.get('thread_id') and entry.thread_id != criteria['thread_id']:
            return False
        if criteria.get('conversation_id') and entry.conversation_id != criteria['conversation_id']:
            return False
        if criteria.get('start_time') and entry.timestamp < criteria['start_time']:
            return False
        if criteria.get('end_time') and entry.timestamp > criteria['end_time']:
            return False
        return True

class SharedMemory:
    """Main shared memory interface."""
    
    def __init__(self, backend: Union[str, MemoryBackend] = "sqlite"):
        """Initialize shared memory with specified backend."""
        if isinstance(backend, str):
            if backend.lower() == "sqlite":
                self.backend = SQLiteBackend()
            elif backend.lower() == "redis":
                self.backend = RedisBackend()
            elif backend.lower() == "memory":
                self.backend = InMemoryBackend()
            else:
                raise ValueError(f"Unknown backend type: {backend}")
        else:
            self.backend = backend
    
    def store(self, 
              source: str,
              type: str,
              extracted_values: Optional[Dict[str, Any]] = None,
              thread_id: Optional[str] = None,
              conversation_id: Optional[str] = None) -> str:
        """Store a new memory entry."""
        entry = MemoryEntry(
            source=source,
            type=type,
            timestamp=datetime.now(),
            thread_id=thread_id,
            conversation_id=conversation_id,
            extracted_values=extracted_values
        )
        return self.backend.store(entry)
    
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID."""
        return self.backend.retrieve(entry_id)
    
    def search(self, **kwargs) -> List[MemoryEntry]:
        """Search for memory entries."""
        return self.backend.search(**kwargs) 