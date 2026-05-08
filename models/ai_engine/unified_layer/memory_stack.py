"""
Memory Stack v0.1
Two-layer memory cache: L0 (short-term, hot) and L1 (context, warm).
Loads identity from vault or SQLite on wake, provides tiered recall.
"""

import os
import re
import sqlite3
from datetime import datetime


def estimate_tokens(text: str) -> int:
    return len(text) // 4


class MemoryStack:
    """Two-layer memory cache with identity loading."""

    def __init__(self, memory_sqlite_path=None, vault_path=None):
        self.memory_sqlite_path = memory_sqlite_path
        self.vault_path = vault_path
        self.conn = None
        if memory_sqlite_path and os.path.exists(memory_sqlite_path):
            self.conn = sqlite3.connect(memory_sqlite_path)
            self.conn.row_factory = sqlite3.Row
        self._l0_cache = None
        self._l1_cache = None

    def _get_identity_from_vault(self):
        if not self.vault_path:
            return None
        profile_path = os.path.join(self.vault_path, "30_Honcho", "User Profile.md")
        if not os.path.exists(profile_path):
            return None
        with open(profile_path, "r", encoding="utf-8") as f:
            content = f.read()
        identity_match = re.search(r"# Identity\s+(.*?)(?=# |$)", content, re.DOTALL)
        prefs_match = re.search(r"# Preferences\s+(.*?)(?=# |$)", content, re.DOTALL)
        identity = identity_match.group(1).strip() if identity_match else ""
        prefs = prefs_match.group(1).strip() if prefs_match else ""
        return f"# Identity\n{identity}\n\n# Preferences\n{prefs}"

    def _get_identity_from_sqlite(self):
        if not self.conn:
            return "AI Assistant"
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT content FROM memory WHERE category IN ('identity', 'preferences') ORDER BY timestamp DESC LIMIT 10")
            rows = cursor.fetchall()
            if rows:
                return "\n".join(row["content"] for row in rows)
        except sqlite3.OperationalError:
            pass
        return "AI Assistant"

    def _load_l0(self, max_tokens=900):
        identity = self._get_identity_from_vault() or self._get_identity_from_sqlite()
        if identity:
            self._l0_cache = identity[:max_tokens]

    def _load_l1(self, max_tokens=500):
        if not self.conn:
            self._l1_cache = ""
            return
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT content FROM memory ORDER BY timestamp DESC LIMIT 20")
            rows = cursor.fetchall()
            parts = [row["content"] for row in rows if row["content"]]
            context = "\n".join(parts)
            max_chars = max_tokens * 4
            self._l1_cache = context[:max_chars] if len(context) > max_chars else context
        except sqlite3.OperationalError:
            self._l1_cache = ""

    def wake_up(self, max_tokens=900):
        self._load_l0(max_tokens=max_tokens)
        self._load_l1()
        return self._l0_cache or ""

    def recall(self, query=None, max_tokens=500):
        parts = []
        if self._l0_cache:
            parts.append(self._l0_cache[:max_tokens * 2])
        if query and self.conn:
            cursor = self.conn.cursor()
            try:
                cursor.execute("SELECT content FROM memory WHERE content LIKE ? ORDER BY timestamp DESC LIMIT 5", (f"%{query}%",))
                rows = cursor.fetchall()
                for row in rows:
                    parts.append(row["content"])
            except sqlite3.OperationalError:
                pass
        max_chars = max_tokens * 4
        result = "\n".join(parts)
        return result[:max_chars] if len(result) > max_chars else result

    def deep_search(self, query, limit=5):
        if not self.conn:
            return []
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT content, category, timestamp FROM memory WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?", (f"%{query}%", limit))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            return []

    def get_layer_sizes(self):
        return {
            "l0": len(self._l0_cache) if self._l0_cache else 0,
            "l1": len(self._l1_cache) if self._l1_cache else 0,
            "estimated_tokens_l0": estimate_tokens(self._l0_cache or ""),
            "estimated_tokens_l1": estimate_tokens(self._l1_cache or ""),
        }

    def inject_context(self, query=None, max_tokens=1000):
        l0 = self._l0_cache or self._get_identity_from_sqlite()
        l1 = ""
        if query:
            results = self.deep_search(query, limit=3)
            l1 = "\n".join(r["content"] for r in results)
        parts = [l0, l1]
        result = "\n".join(p for p in parts if p)
        max_chars = max_tokens * 4
        return result[:max_chars] if len(result) > max_chars else result
