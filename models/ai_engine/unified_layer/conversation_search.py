"""
Conversation Search v1.0 - FTS5 conversation index with LLM summarization.
Based on Hermes Agent FTS5 session search pattern.
Enables cross-session recall and semantic conversation retrieval.
"""

import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from threading import Lock


CONVERSATION_DB_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "conversations"
CONVERSATION_DB_DIR.mkdir(parents=True, exist_ok=True)
CONVERSATION_DB = CONVERSATION_DB_DIR / "conversations.db"


class ConversationSearch:
    """
    SQLite FTS5 conversation index with LLM summarization support.
    Stores and searches conversation turns across sessions.
    """

    def __init__(self, db_path: Path = CONVERSATION_DB):
        self.db_path = db_path
        self._lock = Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS conversations_fts USING fts5(
                        session_id,
                        agent,
                        role,
                        content,
                        summary,
                        tags,
                        content UNINDEXED,
                        tokenize='porter unicode61'
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_metadata (
                        session_id TEXT PRIMARY KEY,
                        agent TEXT,
                        title TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        turn_count INTEGER DEFAULT 0,
                        summary TEXT,
                        tags TEXT DEFAULT '[]'
                    )
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_metadata_agent
                    ON conversation_metadata(agent)
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_metadata_start
                    ON conversation_metadata(start_time)
                """)

                conn.commit()
            except Exception as e:
                print(f"[ConversationSearch] DB init error: {e}")
                conn.rollback()
            finally:
                conn.close()

    def add_turn(
        self,
        session_id: str,
        agent: str,
        role: str,
        content: str,
        summary: str = "",
        tags: Optional[list] = None,
    ) -> bool:
        """Add a conversation turn to the index."""
        with self._lock:
            conn = self._get_conn()
            try:
                tags_json = json.dumps(tags or [])
                conn.execute(
                    "INSERT INTO conversations_fts (session_id, agent, role, content, summary, tags) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (session_id, agent, role, content, summary, tags_json)
                )

                conn.execute(
                    """INSERT OR REPLACE INTO conversation_metadata
                       (session_id, agent, title, start_time, end_time, turn_count, summary, tags)
                       VALUES (?, ?, ?, ?, ?, 
                               COALESCE((SELECT turn_count FROM conversation_metadata WHERE session_id = ?) + 1, 1),
                               ?, ?)""",
                    (session_id, agent, session_id, datetime.now().isoformat(),
                     datetime.now().isoformat(), session_id, "", tags_json)
                )

                conn.commit()
                return True
            except Exception as e:
                print(f"[ConversationSearch] Failed to add turn: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()

    def search(
        self,
        query: str,
        agent: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[dict]:
        """Search conversations using FTS5."""
        with self._lock:
            conn = self._get_conn()
            try:
                sql = """
                    SELECT session_id, agent, role, content, summary, tags, rank
                    FROM conversations_fts
                    WHERE conversations_fts MATCH ?
                """
                params = [query]

                if agent:
                    sql += " AND agent = ?"
                    params.append(agent)

                if session_id:
                    sql += " AND session_id = ?"
                    params.append(session_id)

                sql += " ORDER BY rank LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                rows = conn.execute(sql, params).fetchall()

                results = []
                for row in rows:
                    results.append({
                        "session_id": row["session_id"],
                        "agent": row["agent"],
                        "role": row["role"],
                        "content": row["content"],
                        "summary": row["summary"],
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                        "rank": row["rank"],
                    })

                return results
            except Exception as e:
                print(f"[ConversationSearch] Search error: {e}")
                return []
            finally:
                conn.close()

    def get_session(
        self,
        session_id: str,
        limit: int = 100,
    ) -> List[dict]:
        """Get all turns for a specific session."""
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT session_id, agent, role, content, summary, tags "
                    "FROM conversations_fts WHERE session_id = ? "
                    "ORDER BY rowid LIMIT ?",
                    (session_id, limit)
                ).fetchall()

                return [
                    {
                        "session_id": row["session_id"],
                        "agent": row["agent"],
                        "role": row["role"],
                        "content": row["content"],
                        "summary": row["summary"],
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                    }
                    for row in rows
                ]
            except Exception as e:
                print(f"[ConversationSearch] Get session error: {e}")
                return []
            finally:
                conn.close()

    def get_sessions(
        self,
        agent: Optional[str] = None,
        limit: int = 20,
    ) -> List[dict]:
        """List recent sessions with metadata."""
        with self._lock:
            conn = self._get_conn()
            try:
                sql = """
                    SELECT session_id, agent, title, start_time, end_time,
                           turn_count, summary, tags
                    FROM conversation_metadata
                """
                params = []

                if agent:
                    sql += " WHERE agent = ?"
                    params.append(agent)

                sql += " ORDER BY start_time DESC LIMIT ?"
                params.append(limit)

                rows = conn.execute(sql, params).fetchall()

                return [
                    {
                        "session_id": row["session_id"],
                        "agent": row["agent"],
                        "title": row["title"],
                        "start_time": row["start_time"],
                        "end_time": row["end_time"],
                        "turn_count": row["turn_count"],
                        "summary": row["summary"],
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                    }
                    for row in rows
                ]
            except Exception as e:
                print(f"[ConversationSearch] Get sessions error: {e}")
                return []
            finally:
                conn.close()

    def update_session_summary(self, session_id: str, summary: str) -> bool:
        """Update the LLM-generated summary for a session."""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "UPDATE conversation_metadata SET summary = ? WHERE session_id = ?",
                    (summary, session_id)
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"[ConversationSearch] Update summary error: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()

    def summarize_session(
        self,
        session_id: str,
        transport_chat_fn=None,
        max_turns: int = 50,
    ) -> Optional[str]:
        """
        Generate LLM summary of a conversation session.

        Args:
            session_id: Session to summarize
            transport_chat_fn: Function to call LLM (from UnifiedLayer transport)
            max_turns: Max turns to include in summary prompt

        Returns:
            Generated summary text or None
        """
        if not transport_chat_fn:
            return None

        turns = self.get_session(session_id, limit=max_turns)
        if not turns:
            return None

        conversation_text = "\n".join(
            f"{t['role']}: {t['content'][:200]}" for t in turns
        )

        prompt = f"""Summarize this conversation session in 3-5 sentences. Focus on key decisions, topics discussed, and outcomes.

Conversation:
{conversation_text}

Summary:"""

        try:
            result = transport_chat_fn(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=256,
            )

            summary = result.get("text", "").strip()
            if summary:
                self.update_session_summary(session_id, summary)
                return summary
        except Exception as e:
            print(f"[ConversationSearch] Summarization error: {e}")

        return None

    def delete_session(self, session_id: str) -> bool:
        """Delete all data for a session."""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("DELETE FROM conversations_fts WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM conversation_metadata WHERE session_id = ?", (session_id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"[ConversationSearch] Delete session error: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()

    def get_stats(self) -> dict:
        """Get index statistics."""
        with self._lock:
            conn = self._get_conn()
            try:
                total_turns = conn.execute(
                    "SELECT COUNT(*) as cnt FROM conversations_fts"
                ).fetchone()["cnt"]

                total_sessions = conn.execute(
                    "SELECT COUNT(DISTINCT session_id) as cnt FROM conversations_fts"
                ).fetchone()["cnt"]

                agents = conn.execute(
                    "SELECT DISTINCT agent FROM conversations_fts"
                ).fetchall()

                return {
                    "total_turns": total_turns,
                    "total_sessions": total_sessions,
                    "agents": [row["agent"] for row in agents],
                    "db_size_mb": round(self.db_path.stat().st_size / (1024 * 1024), 2) if self.db_path.exists() else 0,
                }
            except Exception as e:
                print(f"[ConversationSearch] Stats error: {e}")
                return {"total_turns": 0, "total_sessions": 0, "agents": [], "db_size_mb": 0}
            finally:
                conn.close()


_global_search: Optional[ConversationSearch] = None
_search_lock = Lock()


def load_conversation_search() -> ConversationSearch:
    global _global_search
    if _global_search is None:
        with _search_lock:
            if _global_search is None:
                _global_search = ConversationSearch()
    return _global_search
