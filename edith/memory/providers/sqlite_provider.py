"""
SQLite Provider for Long-Term Memory.
"""

import sqlite3
import json
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from edith.memory.memory_models import Memory, MemoryRelationship, MemoryCategory
from edith.memory.memory_constants import MemorySource
from edith.memory.memory_exceptions import MemoryNotFoundError, ProviderNotAvailableError
from edith.utils.logger import logger

class ISqliteProvider(ABC):
    @abstractmethod
    def initialize(self) -> None:
        pass
        
    @abstractmethod
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        pass
        
    @abstractmethod
    def save_memory(self, memory: Memory) -> None:
        pass
        
    @abstractmethod
    def delete_memory(self, memory_id: str) -> None:
        pass
        
    @abstractmethod
    def list_memories(self, category: Optional[MemoryCategory] = None) -> List[Memory]:
        pass

    @abstractmethod
    def save_relationship(self, rel: MemoryRelationship) -> None:
        pass

    @abstractmethod
    def get_relationships(self, source_id: str) -> List[MemoryRelationship]:
        pass


class SqliteProvider(ISqliteProvider):
    def __init__(self, db_path: str = "edith_ltm.db"):
        self.db_path = db_path
        self._memory_conn = None
        
    def _get_conn(self) -> sqlite3.Connection:
        try:
            if self.db_path == ":memory:":
                if not self._memory_conn:
                    self._memory_conn = sqlite3.connect(self.db_path, check_same_thread=False)
                    self._memory_conn.row_factory = sqlite3.Row
                return self._memory_conn
                
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise ProviderNotAvailableError(f"SQLite error: {e}")

    def initialize(self) -> None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Memories Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    value TEXT NOT NULL,
                    metadata TEXT,
                    confidence REAL,
                    importance REAL,
                    created_time TIMESTAMP,
                    updated_time TIMESTAMP,
                    last_accessed TIMESTAMP,
                    access_count INTEGER,
                    embedding_id TEXT,
                    ttl TIMESTAMP,
                    source TEXT
                )
            ''')
            
            # Tags Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_tags (
                    memory_id TEXT,
                    tag TEXT,
                    FOREIGN KEY (memory_id) REFERENCES memories (id) ON DELETE CASCADE
                )
            ''')
            
            # Relationships Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_relationships (
                    source_id TEXT,
                    target_id TEXT,
                    relation_type TEXT,
                    FOREIGN KEY (source_id) REFERENCES memories (id) ON DELETE CASCADE,
                    FOREIGN KEY (target_id) REFERENCES memories (id) ON DELETE CASCADE,
                    PRIMARY KEY (source_id, target_id, relation_type)
                )
            ''')
            
            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_category ON memories(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_tags ON memory_tags(tag)")
            conn.commit()

    def _row_to_memory(self, row: sqlite3.Row, tags: List[str]) -> Memory:
        return Memory(
            id=row["id"],
            category=MemoryCategory(row["category"]),
            title=row["title"],
            value=row["value"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            confidence=row["confidence"],
            importance=row["importance"],
            created_time=datetime.fromisoformat(row["created_time"]),
            updated_time=datetime.fromisoformat(row["updated_time"]),
            last_accessed=datetime.fromisoformat(row["last_accessed"]),
            access_count=row["access_count"],
            embedding_id=row["embedding_id"],
            ttl=datetime.fromisoformat(row["ttl"]) if row["ttl"] else None,
            source=MemorySource(row["source"]),
            tags=tags
        )

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            if not row:
                return None
                
            cursor.execute("SELECT tag FROM memory_tags WHERE memory_id = ?", (memory_id,))
            tags = [r["tag"] for r in cursor.fetchall()]
            
            return self._row_to_memory(row, tags)

    def save_memory(self, memory: Memory) -> None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO memories (
                    id, category, title, value, metadata, confidence, importance,
                    created_time, updated_time, last_accessed, access_count,
                    embedding_id, ttl, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    category=excluded.category,
                    title=excluded.title,
                    value=excluded.value,
                    metadata=excluded.metadata,
                    confidence=excluded.confidence,
                    importance=excluded.importance,
                    updated_time=excluded.updated_time,
                    last_accessed=excluded.last_accessed,
                    access_count=excluded.access_count,
                    embedding_id=excluded.embedding_id,
                    ttl=excluded.ttl,
                    source=excluded.source
            ''', (
                memory.id,
                memory.category.value,
                memory.title,
                memory.value,
                json.dumps(memory.metadata),
                memory.confidence,
                memory.importance,
                memory.created_time.isoformat(),
                memory.updated_time.isoformat(),
                memory.last_accessed.isoformat(),
                memory.access_count,
                memory.embedding_id,
                memory.ttl.isoformat() if memory.ttl else None,
                memory.source.value
            ))
            
            # Update tags
            cursor.execute("DELETE FROM memory_tags WHERE memory_id = ?", (memory.id,))
            if memory.tags:
                tag_rows = [(memory.id, tag) for tag in memory.tags]
                cursor.executemany("INSERT INTO memory_tags (memory_id, tag) VALUES (?, ?)", tag_rows)
            
            conn.commit()

    def delete_memory(self, memory_id: str) -> None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            if cursor.rowcount == 0:
                raise MemoryNotFoundError(f"Memory {memory_id} not found.")
            # Note: memory_tags and memory_relationships are CASCADE deleted.
            conn.commit()

    def list_memories(self, category: Optional[MemoryCategory] = None) -> List[Memory]:
        memories = []
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute("SELECT * FROM memories WHERE category = ?", (category.value,))
            else:
                cursor.execute("SELECT * FROM memories")
            
            rows = cursor.fetchall()
            for row in rows:
                cursor.execute("SELECT tag FROM memory_tags WHERE memory_id = ?", (row["id"],))
                tags = [r["tag"] for r in cursor.fetchall()]
                memories.append(self._row_to_memory(row, tags))
                
        return memories

    def save_relationship(self, rel: MemoryRelationship) -> None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO memory_relationships (source_id, target_id, relation_type)
                VALUES (?, ?, ?)
            ''', (rel.source_id, rel.target_id, rel.relation_type))
            conn.commit()

    def get_relationships(self, source_id: str) -> List[MemoryRelationship]:
        rels = []
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memory_relationships WHERE source_id = ?", (source_id,))
            for row in cursor.fetchall():
                rels.append(MemoryRelationship(
                    source_id=row["source_id"],
                    target_id=row["target_id"],
                    relation_type=row["relation_type"]
                ))
        return rels
