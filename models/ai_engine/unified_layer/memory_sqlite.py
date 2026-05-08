"""
SQLite Memory Backend - Phase 1 of Architecture Evolution
Combines SQLite FTS5 (full-text search) with sqlite-vec (vector similarity search)
for fast, persistent memory across all agents.

Augments (doesn't replace) DCTPMemory and existing shared_memory.json.
"""

import json
import os
import sqlite3
import time
import struct
import numpy as np
from pathlib import Path
from datetime import datetime
from threading import Lock
from typing import List, Optional, Dict, Any

DB_PATH = Path(
    r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\memory\unified_memory.db"
)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
LOCK = Lock()

USE_SENTENCE_TRANSFORMERS = False
EMBEDDING_MODEL = None

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    USE_SENTENCE_TRANSFORMERS = True
    print(f"[SQLiteMemory] Loaded all-MiniLM-L6-v2 for embeddings")
except Exception:
    print("[SQLiteMemory] Embedding model unavailable, using TF-IDF fallback")


def get_embedding(text: str) -> Optional[List[float]]:
    """Generate a 384-dim embedding for text."""
    if USE_SENTENCE_TRANSFORMERS:
        vec = EMBEDDING_MODEL.encode([text])[0]
        return vec.tolist()
    return None


def serialize_vector(vec: List[float]) -> bytes:
    """Pack float list into binary for sqlite-vec."""
    return struct.pack(f"{len(vec)}f", *vec)


def _safe_fts_query(query: str) -> str:
    """Sanitize query for FTS5 (escape special chars)."""
    safe = query.replace(".", " ").replace("-", " ").replace("(", " ").replace(")", " ")
    safe = safe.replace("[", " ").replace("]", " ").replace("{", " ").replace("}", " ")
    return " OR ".join(safe.split())


class SQLiteMemory:
    """
    Unified SQLite memory backend with:
    - FTS5 full-text search over all entries
    - Vector similarity search via sqlite-vec
    - Conversation log storage
    - Agent memory storage
    - Cross-session search
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """Initialize database tables, FTS5, and vector virtual table."""
        with LOCK:
            cur = self.conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created TEXT NOT NULL,
                    updated TEXT NOT NULL,
                    ttl INTEGER,
                    embedding BLOB,
                    embedding_dim INTEGER
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    embedding BLOB,
                    embedding_dim INTEGER
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    code TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    last_used TEXT,
                    embedding BLOB,
                    embedding_dim INTEGER
                )
            """)

            cur.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts
                USING fts5(value, key, category, content='memory_entries', content_rowid='id')
            """)

            cur.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS conversation_fts
                USING fts5(content, role, content='conversations', content_rowid='id')
            """)

            cur.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS skill_fts
                USING fts5(name, description, category, code, content='skills', content_rowid='id')
            """)

            try:
                import sqlite_vec
                self.conn.enable_load_extension(True)
                sqlite_vec.load(self.conn)
                self.conn.enable_load_extension(False)

                cur.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS memory_vec
                    USING vec0(embedding float[384])
                """)

                cur.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS conversation_vec
                    USING vec0(embedding float[384])
                """)

                cur.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS skill_vec
                    USING vec0(embedding float[384])
                """)

                self.vec_enabled = True
                print("[SQLiteMemory] sqlite-vec loaded (vector search active)")
            except Exception as e:
                self.vec_enabled = False
                print(f"[SQLiteMemory] sqlite-vec unavailable ({e}), FTS5 only")

            cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_agent ON memory_entries(agent)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_category ON memory_entries(category)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_key ON memory_entries(key)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_conv_agent ON conversations(agent)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id)")

            cur.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_ai AFTER INSERT ON memory_entries BEGIN
                    INSERT INTO memory_fts(rowid, value, key, category)
                    VALUES (new.id, new.value, new.key, new.category);
                END
            """)

            cur.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_ad AFTER DELETE ON memory_entries BEGIN
                    INSERT INTO memory_fts(memory_fts, rowid, value, key, category)
                    VALUES ('delete', old.id, old.value, old.key, old.category);
                END
            """)

            cur.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_au AFTER UPDATE ON memory_entries BEGIN
                    INSERT INTO memory_fts(memory_fts, rowid, value, key, category)
                    VALUES ('delete', old.id, old.value, old.key, old.category);
                    INSERT INTO memory_fts(rowid, value, key, category)
                    VALUES (new.id, new.value, new.key, new.category);
                END
            """)

            cur.execute("""
                CREATE TRIGGER IF NOT EXISTS conv_ai AFTER INSERT ON conversations BEGIN
                    INSERT INTO conversation_fts(rowid, content, role)
                    VALUES (new.id, new.content, new.role);
                END
            """)

            cur.execute("""
                CREATE TRIGGER IF NOT EXISTS conv_ad AFTER DELETE ON conversations BEGIN
                    INSERT INTO conversation_fts(conversation_fts, rowid, content, role)
                    VALUES ('delete', old.id, old.content, old.role);
                END
            """)

            cur.execute("""
                CREATE TRIGGER IF NOT EXISTS conv_au AFTER UPDATE ON conversations BEGIN
                    INSERT INTO conversation_fts(conversation_fts, rowid, content, role)
                    VALUES ('delete', old.id, old.content, old.role);
                    INSERT INTO conversation_fts(rowid, content, role)
                    VALUES (new.id, new.content, new.role);
                END
            """)

            self.conn.commit()

    def store_memory(
        self,
        agent: str,
        key: str,
        value: str,
        category: str = "general",
        ttl: Optional[int] = None,
    ) -> int:
        """Store a memory entry with optional embedding."""
        now = datetime.now().isoformat()
        embedding = get_embedding(value) if USE_SENTENCE_TRANSFORMERS else None

        with LOCK:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT INTO memory_entries (agent, key, value, category, created, updated, ttl, embedding, embedding_dim)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (agent, key, value, category, now, now, ttl,
                 serialize_vector(embedding) if embedding else None,
                 len(embedding) if embedding else None),
            )
            entry_id = cur.lastrowid

            if embedding and self.vec_enabled:
                cur.execute(
                    "INSERT INTO memory_vec(rowid, embedding) VALUES (?, ?)",
                    (entry_id, serialize_vector(embedding)),
                )

            self.conn.commit()
            return entry_id

    def store_conversation(
        self,
        agent: str,
        session_id: str,
        role: str,
        content: str,
    ) -> int:
        """Store a conversation turn with optional embedding."""
        now = datetime.now().isoformat()
        embedding = get_embedding(content) if USE_SENTENCE_TRANSFORMERS else None

        with LOCK:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT INTO conversations (agent, session_id, role, content, timestamp, embedding, embedding_dim)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (agent, session_id, role, content, now,
                 serialize_vector(embedding) if embedding else None,
                 len(embedding) if embedding else None),
            )
            entry_id = cur.lastrowid

            if embedding and self.vec_enabled:
                cur.execute(
                    "INSERT INTO conversation_vec(rowid, embedding) VALUES (?, ?)",
                    (entry_id, serialize_vector(embedding)),
                )

            self.conn.commit()
            return entry_id

    def store_skill(
        self,
        name: str,
        description: str,
        code: str,
        category: str = "general",
    ) -> int:
        """Store a reusable skill."""
        now = datetime.now().isoformat()
        embedding = get_embedding(f"{name} {description}") if USE_SENTENCE_TRANSFORMERS else None

        with LOCK:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO skills (name, description, code, category, created, usage_count, embedding, embedding_dim)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (name, description, code, category, now,
                 serialize_vector(embedding) if embedding else None,
                 len(embedding) if embedding else None),
            )
            skill_id = cur.lastrowid

            if embedding and self.vec_enabled:
                cur.execute(
                    "INSERT INTO skill_vec(rowid, embedding) VALUES (?, ?)",
                    (skill_id, serialize_vector(embedding)),
                )

            self.conn.commit()
            return skill_id

    def search_memory(
        self,
        query: str,
        category: Optional[str] = None,
        agent: Optional[str] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search memories using FTS5 + vector similarity (hybrid)."""
        results = []

        with LOCK:
            cur = self.conn.cursor()
            fts_query = _safe_fts_query(query)
            where_clause = ""
            params = [fts_query]

            if category:
                where_clause += " AND category = ?"
                params.append(category)
            if agent:
                where_clause += " AND agent = ?"
                params.append(agent)

            cur.execute(
                f"""
                SELECT m.id, m.agent, m.key, m.value, m.category, m.created, m.updated,
                       rank as fts_rank
                FROM memory_fts
                JOIN memory_entries m ON m.id = memory_fts.rowid
                WHERE memory_fts MATCH ?
                {where_clause}
                ORDER BY rank
                LIMIT ?
                """,
                params + [max_results],
            )

            for row in cur.fetchall():
                results.append({
                    "type": "memory",
                    "id": row["id"],
                    "agent": row["agent"],
                    "key": row["key"],
                    "value": row["value"],
                    "category": row["category"],
                    "created": row["created"],
                    "updated": row["updated"],
                    "fts_rank": row["fts_rank"],
                })

        if self.vec_enabled and USE_SENTENCE_TRANSFORMERS:
            query_vec = get_embedding(query)
            if query_vec:
                vec_data = serialize_vector(query_vec)
                with LOCK:
                    cur = self.conn.cursor()
                    cur.execute(
                        "SELECT rowid, distance FROM memory_vec WHERE embedding MATCH ? AND k = ?",
                        (vec_data, max_results),
                    )
                    for row in cur.fetchall():
                        existing_ids = {r["id"] for r in results if r["type"] == "memory"}
                        if row["rowid"] not in existing_ids:
                            cur2 = self.conn.cursor()
                            cur2.execute("SELECT * FROM memory_entries WHERE id = ?", (row["rowid"],))
                            mem = cur2.fetchone()
                            if mem:
                                results.append({
                                    "type": "memory",
                                    "id": mem["id"],
                                    "agent": mem["agent"],
                                    "key": mem["key"],
                                    "value": mem["value"],
                                    "category": mem["category"],
                                    "created": mem["created"],
                                    "updated": mem["updated"],
                                    "vec_distance": row["distance"],
                                })

        return results[:max_results]

    def search_conversations(
        self,
        query: str,
        agent: Optional[str] = None,
        session_id: Optional[str] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search conversation history using FTS5 + vector."""
        results = []

        with LOCK:
            cur = self.conn.cursor()
            fts_query = _safe_fts_query(query)
            where_clause = ""
            params = [fts_query]

            if agent:
                where_clause += " AND agent = ?"
                params.append(agent)
            if session_id:
                where_clause += " AND session_id = ?"
                params.append(session_id)

            cur.execute(
                f"""
                SELECT c.id, c.agent, c.session_id, c.role, c.content, c.timestamp,
                       rank as fts_rank
                FROM conversation_fts
                JOIN conversations c ON c.id = conversation_fts.rowid
                WHERE conversation_fts MATCH ?
                {where_clause}
                ORDER BY rank
                LIMIT ?
                """,
                params + [max_results],
            )

            for row in cur.fetchall():
                results.append({
                    "type": "conversation",
                    "id": row["id"],
                    "agent": row["agent"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"],
                    "fts_rank": row["fts_rank"],
                })

        if self.vec_enabled and USE_SENTENCE_TRANSFORMERS:
            query_vec = get_embedding(query)
            if query_vec:
                vec_data = serialize_vector(query_vec)
                with LOCK:
                    cur = self.conn.cursor()
                    cur.execute(
                        "SELECT rowid, distance FROM conversation_vec WHERE embedding MATCH ? AND k = ?",
                        (vec_data, max_results),
                    )
                    for row in cur.fetchall():
                        existing_ids = {r["id"] for r in results if r["type"] == "conversation"}
                        if row["rowid"] not in existing_ids:
                            cur2 = self.conn.cursor()
                            cur2.execute("SELECT * FROM conversations WHERE id = ?", (row["rowid"],))
                            conv = cur2.fetchone()
                            if conv:
                                results.append({
                                    "type": "conversation",
                                    "id": conv["id"],
                                    "agent": conv["agent"],
                                    "session_id": conv["session_id"],
                                    "role": conv["role"],
                                    "content": conv["content"],
                                    "timestamp": conv["timestamp"],
                                    "vec_distance": row["distance"],
                                })

        return results[:max_results]

    def search_skills(
        self,
        query: str,
        category: Optional[str] = None,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search reusable skills."""
        results = []

        with LOCK:
            cur = self.conn.cursor()
            fts_query = _safe_fts_query(query)
            where_clause = ""
            params = [fts_query]

            if category:
                where_clause += " AND category = ?"
                params.append(category)

            cur.execute(
                f"""
                SELECT s.id, s.name, s.description, s.code, s.category,
                       s.created, s.usage_count, s.last_used,
                       rank as fts_rank
                FROM skill_fts
                JOIN skills s ON s.id = skill_fts.rowid
                WHERE skill_fts MATCH ?
                {where_clause}
                ORDER BY rank
                LIMIT ?
                """,
                params + [max_results],
            )

            for row in cur.fetchall():
                results.append({
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "code": row["code"],
                    "category": row["category"],
                    "created": row["created"],
                    "usage_count": row["usage_count"],
                    "last_used": row["last_used"],
                    "fts_rank": row["fts_rank"],
                })

        if self.vec_enabled and USE_SENTENCE_TRANSFORMERS:
            query_vec = get_embedding(query)
            if query_vec:
                vec_data = serialize_vector(query_vec)
                with LOCK:
                    cur = self.conn.cursor()
                    cur.execute(
                        "SELECT rowid, distance FROM skill_vec WHERE embedding MATCH ? AND k = ?",
                        (vec_data, max_results),
                    )
                    for row in cur.fetchall():
                        if row["rowid"] not in {r["id"] for r in results}:
                            cur2 = self.conn.cursor()
                            cur2.execute("SELECT * FROM skills WHERE id = ?", (row["rowid"],))
                            skill = cur2.fetchone()
                            if skill:
                                results.append({
                                    "id": skill["id"],
                                    "name": skill["name"],
                                    "description": skill["description"],
                                    "code": skill["code"],
                                    "category": skill["category"],
                                    "created": skill["created"],
                                    "usage_count": skill["usage_count"],
                                    "last_used": skill["last_used"],
                                    "vec_distance": row["distance"],
                                })

        return results[:max_results]

    def get_memories_by_agent(
        self, agent: str, category: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get all memories from a specific agent."""
        with LOCK:
            cur = self.conn.cursor()
            q = "SELECT * FROM memory_entries WHERE agent = ?"
            params: list = [agent]

            if category:
                q += " AND category = ?"
                params.append(category)

            q += " ORDER BY updated DESC LIMIT ?"
            params.append(limit)

            cur.execute(q, params)
            return [dict(row) for row in cur.fetchall()]

    def get_recent_conversations(
        self, agent: Optional[str] = None, session_id: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent conversation turns."""
        with LOCK:
            cur = self.conn.cursor()
            q = "SELECT * FROM conversations WHERE 1=1"
            params: list = []

            if agent:
                q += " AND agent = ?"
                params.append(agent)
            if session_id:
                q += " AND session_id = ?"
                params.append(session_id)

            q += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cur.execute(q, params)
            return [dict(row) for row in cur.fetchall()]

    def cleanup_expired(self) -> int:
        """Remove expired TTL entries."""
        now = time.time()
        with LOCK:
            cur = self.conn.cursor()
            cur.execute("SELECT id, ttl, created FROM memory_entries WHERE ttl IS NOT NULL")
            expired = []
            for row in cur.fetchall():
                created_ts = datetime.fromisoformat(row["created"]).timestamp()
                if created_ts + row["ttl"] < now:
                    expired.append(row["id"])

            if expired:
                placeholders = ",".join("?" * len(expired))
                cur.execute(f"DELETE FROM memory_entries WHERE id IN ({placeholders})", expired)
                self.conn.commit()

            return len(expired)

    def get_stats(self) -> Dict[str, Any]:
        """Get memory database statistics."""
        with LOCK:
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM memory_entries")
            memory_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM conversations")
            conv_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM skills")
            skill_count = cur.fetchone()[0]

            cur.execute("SELECT DISTINCT category FROM memory_entries")
            categories = [row[0] for row in cur.fetchall()]

            return {
                "memory_entries": memory_count,
                "conversations": conv_count,
                "skills": skill_count,
                "categories": categories,
                "vector_search": self.vec_enabled,
                "embeddings": USE_SENTENCE_TRANSFORMERS,
                "db_size_mb": round(self.db_path.stat().st_size / (1024 * 1024), 2)
                if self.db_path.exists()
                else 0,
            }

    def close(self):
        """Close database connection."""
        with LOCK:
            self.conn.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


def load_sqlite_memory(db_path: Optional[Path] = None) -> SQLiteMemory:
    """Factory function."""
    return SQLiteMemory(db_path)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis")

    mem = load_sqlite_memory()

    print("=== SQLite Memory Backend ===")
    stats = mem.get_stats()
    print(f"Memory entries: {stats['memory_entries']}")
    print(f"Conversations: {stats['conversations']}")
    print(f"Skills: {stats['skills']}")
    print(f"Vector search: {stats['vector_search']}")
    print(f"DB size: {stats['db_size_mb']}MB")

    print("\n=== Test: Store Memories ===")
    mem.store_memory("opencode", "test_key", "This is a test memory entry about SQLite", "test")
    mem.store_memory("omnis", "user_pref", "User prefers dark mode and casual tone", "preference")
    mem.store_memory("jarvis", "session_note", "Discussed architecture evolution with Stef", "context")

    print("\n=== Test: FTS5 Search ===")
    results = mem.search_memory("user preferences", max_results=5)
    for r in results:
        print(f"  [{r['category']}] {r['key']}: {r['value'][:60]}")

    print("\n=== Final Stats ===")
    stats = mem.get_stats()
    print(json.dumps(stats, indent=2))

    mem.close()
