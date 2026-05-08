"""
Sync State Tracker — Tracks mining progress to skip unchanged files.
Inspired by MegaMem's sync.db content hashing system.

Stores: (source_type, file_path, content_hash, last_mined, triples_added)
"""

import hashlib
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class SyncTracker:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = DATA_DIR / "mining_state.db"
        self.db_path = str(db_path)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mining_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                last_mined TEXT NOT NULL,
                triples_added INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'success',
                UNIQUE(source_type, file_path)
            );
            CREATE INDEX IF NOT EXISTS idx_sync_hash ON mining_state(content_hash);
            CREATE INDEX IF NOT EXISTS idx_sync_type ON mining_state(source_type);
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def hash_content(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()

    def should_mine(self, source_type: str, file_path: str, content: str) -> bool:
        """Check if a file needs mining. Returns False if content hasn't changed."""
        new_hash = self.hash_content(content)
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cur = conn.execute(
                "SELECT content_hash FROM mining_state WHERE source_type = ? AND file_path = ?",
                (source_type, file_path)
            )
            row = cur.fetchone()
            conn.close()
        if row and row[0] == new_hash:
            return False
        return True

    def mark_mined(self, source_type: str, file_path: str, content: str,
                   triples_added: int = 0, status: str = "success"):
        """Record that a file was mined. Upserts the mining_state row."""
        new_hash = self.hash_content(content)
        now = datetime.utcnow().isoformat()
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """INSERT INTO mining_state (source_type, file_path, content_hash, last_mined, triples_added, status)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(source_type, file_path) DO UPDATE SET
                       content_hash = excluded.content_hash,
                       last_mined = excluded.last_mined,
                       triples_added = excluded.triples_added,
                       status = excluded.status""",
                (source_type, file_path, new_hash, now, triples_added, status)
            )
            conn.commit()
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get sync state statistics."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            total = conn.execute("SELECT COUNT(*) FROM mining_state").fetchone()[0]
            by_type = dict(conn.execute(
                "SELECT source_type, COUNT(*) FROM mining_state GROUP BY source_type"
            ).fetchall())
            total_triples = conn.execute(
                "SELECT SUM(triples_added) FROM mining_state"
            ).fetchone()[0] or 0
            latest = conn.execute(
                "SELECT last_mined FROM mining_state ORDER BY last_mined DESC LIMIT 1"
            ).fetchone()
            conn.close()
        return {
            "total_files_tracked": total,
            "by_source_type": by_type,
            "total_triples_from_mining": total_triples,
            "last_mined_at": latest[0] if latest else None,
        }

    def get_mined_files(self, source_type: Optional[str] = None) -> list:
        """Get list of already-mined files."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            if source_type:
                cur = conn.execute(
                    "SELECT file_path, content_hash, last_mined FROM mining_state WHERE source_type = ?",
                    (source_type,)
                )
            else:
                cur = conn.execute(
                    "SELECT source_type, file_path, content_hash, last_mined FROM mining_state"
                )
            rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
            conn.close()
        return rows

    def reset_file(self, source_type: str, file_path: str):
        """Force re-mine a specific file by removing its sync record."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "DELETE FROM mining_state WHERE source_type = ? AND file_path = ?",
                (source_type, file_path)
            )
            conn.commit()
            conn.close()

    def reset_all(self, source_type: Optional[str] = None):
        """Reset sync state for all files (or a specific source type)."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            if source_type:
                conn.execute("DELETE FROM mining_state WHERE source_type = ?", (source_type,))
            else:
                conn.execute("DELETE FROM mining_state")
            conn.commit()
            conn.close()


_sync_instance = None
_sync_lock = threading.Lock()


def get_sync_tracker() -> SyncTracker:
    global _sync_instance
    if _sync_instance is None:
        with _sync_lock:
            if _sync_instance is None:
                _sync_instance = SyncTracker()
    return _sync_instance
