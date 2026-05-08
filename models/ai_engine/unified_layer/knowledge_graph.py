import sqlite3
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


def _normalize(name: str) -> str:
    return name.lower().replace(" ", "_")


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


class KnowledgeGraph:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Path(__file__).parent / "data" / "knowledge_graph.db"
        self.db_path = str(db_path)
        self._lock = threading.Lock()
        with self._lock:
            self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'concept',
                properties TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS triples (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                valid_from TEXT NOT NULL,
                valid_to TEXT,
                confidence REAL NOT NULL DEFAULT 1.0,
                source TEXT DEFAULT '',
                FOREIGN KEY(subject) REFERENCES entities(id)
            );

            CREATE INDEX IF NOT EXISTS idx_triples_subject ON triples(subject);
            CREATE INDEX IF NOT EXISTS idx_triples_predicate ON triples(predicate);
            CREATE INDEX IF NOT EXISTS idx_triples_valid ON triples(valid_from, valid_to);
        """)
        conn.executescript("""
            CREATE VIRTUAL TABLE IF NOT EXISTS triples_fts USING fts5(
                subject, predicate, object,
                content=triples,
                content_rowid=rowid
            );

            CREATE TRIGGER IF NOT EXISTS triples_after_insert
            AFTER INSERT ON triples
            BEGIN
                INSERT INTO triples_fts(rowid, subject, predicate, object)
                VALUES (new.rowid, new.subject, new.predicate, new.object);
            END;

            CREATE TRIGGER IF NOT EXISTS triples_after_delete
            AFTER DELETE ON triples
            BEGIN
                INSERT INTO triples_fts(triples_fts, rowid, subject, predicate, object)
                VALUES ('delete', old.rowid, old.subject, old.predicate, old.object);
            END;

            CREATE TRIGGER IF NOT EXISTS triples_after_update
            AFTER UPDATE ON triples
            BEGIN
                INSERT INTO triples_fts(triples_fts, rowid, subject, predicate, object)
                VALUES ('delete', old.rowid, old.subject, old.predicate, old.object);
                INSERT INTO triples_fts(rowid, subject, predicate, object)
                VALUES (new.rowid, new.subject, new.predicate, new.object);
            END;
        """)
        conn.commit()
        conn.close()

    def _ensure_entity(self, conn, entity_id: str, display_name: Optional[str] = None, entity_type: str = "concept"):
        cur = conn.execute("SELECT id FROM entities WHERE id = ?", (entity_id,))
        if cur.fetchone() is None:
            name = display_name or entity_id.replace("_", " ").title()
            conn.execute(
                "INSERT INTO entities (id, name, type, properties) VALUES (?, ?, ?, ?)",
                (entity_id, name, entity_type, json.dumps({}))
            )

    def add_triple(self, subject: str, predicate: str, obj: str,
                   valid_from: Optional[str] = None, confidence: float = 1.0,
                   source: str = "") -> int:
        subject_id = _normalize(subject)
        now = valid_from or _now_iso()
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            self._ensure_entity(conn, subject_id, display_name=subject)
            cur = conn.execute(
                "INSERT INTO triples (subject, predicate, object, valid_from, valid_to, confidence, source) "
                "VALUES (?, ?, ?, ?, NULL, ?, ?)",
                (subject_id, predicate, obj, now, confidence, source)
            )
            rowid = cur.lastrowid
            conn.commit()
            conn.close()
        return rowid

    def invalidate(self, subject: str, predicate: str, obj: str, ended: Optional[str] = None):
        subject_id = _normalize(subject)
        now = ended or _now_iso()
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "UPDATE triples SET valid_to = ? "
                "WHERE subject = ? AND predicate = ? AND object = ? AND valid_to IS NULL",
                (now, subject_id, predicate, obj)
            )
            conn.commit()
            conn.close()

    def query_entity(self, entity_id: str, as_of: Optional[str] = None) -> List[Dict[str, Any]]:
        entity_id = _normalize(entity_id)
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            if as_of is None:
                cur = conn.execute(
                    "SELECT * FROM triples WHERE subject = ? AND valid_to IS NULL ORDER BY valid_from",
                    (entity_id,)
                )
            else:
                cur = conn.execute(
                    "SELECT * FROM triples WHERE subject = ? AND valid_from <= ? AND (valid_to IS NULL OR valid_to > ?) "
                    "ORDER BY valid_from",
                    (entity_id, as_of, as_of)
                )
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
        return rows

    def query_by_predicate(self, predicate: str, as_of: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            if as_of is None:
                cur = conn.execute(
                    "SELECT * FROM triples WHERE predicate = ? AND valid_to IS NULL ORDER BY valid_from",
                    (predicate,)
                )
            else:
                cur = conn.execute(
                    "SELECT * FROM triples WHERE predicate = ? AND valid_from <= ? AND (valid_to IS NULL OR valid_to > ?) "
                    "ORDER BY valid_from",
                    (predicate, as_of, as_of)
                )
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
        return rows

    def timeline(self, entity_id: str) -> List[Dict[str, Any]]:
        entity_id = _normalize(entity_id)
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT * FROM triples WHERE subject = ? ORDER BY valid_from",
                (entity_id,)
            )
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
        return rows

    def query_all_current(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT * FROM triples WHERE valid_to IS NULL ORDER BY subject, valid_from"
            )
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
        return rows

    def delete_entity(self, entity_id: str):
        entity_id = _normalize(entity_id)
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM triples WHERE subject = ?", (entity_id,))
            conn.execute("DELETE FROM entities WHERE id = ?", (entity_id,))
            conn.commit()
            conn.close()

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            ec = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            tc = conn.execute("SELECT COUNT(*) FROM triples").fetchone()[0]
            types = dict(conn.execute("SELECT type, COUNT(*) FROM entities GROUP BY type").fetchall())
            preds = dict(conn.execute("SELECT predicate, COUNT(*) FROM triples GROUP BY predicate").fetchall())
            conn.close()
        return {
            "entity_count": ec,
            "triple_count": tc,
            "types_breakdown": types,
            "predicate_breakdown": preds,
        }

    def search(self, query_text: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT t.* FROM triples_fts f "
                "JOIN triples t ON t.rowid = f.rowid "
                "WHERE triples_fts MATCH ? ORDER BY rank",
                (query_text,)
            )
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
        return rows
