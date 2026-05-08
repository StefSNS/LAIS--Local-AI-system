import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

from knowledge_graph import KnowledgeGraph, _normalize


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


class TunnelManager:
    """
    MemPalace-inspired 'tunnels' — cross-wing connections linking related topics
    across different people/projects (wings).

    A tunnel exists when the same 'room' (topic/category) appears in multiple 'wings' (entities).
    """

    def __init__(self, knowledge_graph_path=None, db_path=None):
        if knowledge_graph_path:
            self.kg = KnowledgeGraph(knowledge_graph_path)
        else:
            self.kg = KnowledgeGraph()

        if db_path is None:
            db_path = Path(__file__).parent / "data" / "tunnels.db"
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_gemini()
        self._init_db()

    def _init_gemini(self):
        self.gemini = None
        try:
            from utils.api_keys import GEMINI_API_KEY
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini = genai.GenerativeModel('gemini-2.5-flash-lite')
        except (ImportError, ModuleNotFoundError):
            pass

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tunnels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_name TEXT NOT NULL,
                wing_a TEXT NOT NULL,
                wing_b TEXT NOT NULL,
                connection_type TEXT NOT NULL DEFAULT 'shared_topic',
                strength REAL NOT NULL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                UNIQUE(room_name, wing_a, wing_b)
            );

            CREATE INDEX IF NOT EXISTS idx_tunnels_room ON tunnels(room_name);
            CREATE INDEX IF NOT EXISTS idx_tunnels_wing_a ON tunnels(wing_a);
            CREATE INDEX IF NOT EXISTS idx_tunnels_wing_b ON tunnels(wing_b);
        """)
        conn.commit()
        conn.close()

    def _classify_tunnel_type(self, room_name: str, wing_a: str, wing_b: str,
                              triples_a: List[Dict], triples_b: List[Dict]) -> str:
        if not self.gemini:
            return "shared_topic"

        preds_a = [t["predicate"] for t in triples_a]
        preds_b = [t["predicate"] for t in triples_b]
        objs_a = [t["object"] for t in triples_a]
        objs_b = [t["object"] for t in triples_b]

        prompt = f"""Classify the connection type between two wings sharing topic '{room_name}':

Wing A: {wing_a}
- Predicates: {preds_a}
- Objects: {objs_a}

Wing B: {wing_b}
- Predicates: {preds_b}
- Objects: {objs_b}

Choose exactly one from:
- shared_topic: same topic exists independently in both wings
- dependency: one wing depends on or uses the other's work on this topic
- influence: one wing's treatment of the topic influenced the other
- conflict: the wings have opposing views or approaches to the topic

Return only the connection type string, nothing else."""

        try:
            response = self.gemini.generate_content(prompt)
            result = response.text.strip().lower()
            if result in ("shared_topic", "dependency", "influence", "conflict"):
                return result
        except Exception:
            pass
        return "shared_topic"

    def discover_tunnels(self) -> List[Dict[str, Any]]:
        all_triples = self.kg.query_all_current()

        room_wings = defaultdict(list)
        for t in all_triples:
            room = t["subject"]
            wing = t.get("source", "unknown")
            if wing and wing != "unknown":
                room_wings[room].append(wing)

        tunnels = []
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM tunnels")

        for room, wings in room_wings.items():
            unique_wings = list(set(wings))
            if len(unique_wings) < 2:
                continue

            for i, wing_a in enumerate(unique_wings):
                for wing_b in unique_wings[i+1:]:
                    triples_a = [t for t in all_triples
                                 if t["subject"] == room and t.get("source") == wing_a]
                    triples_b = [t for t in all_triples
                                 if t["subject"] == room and t.get("source") == wing_b]

                    conn_type = self._classify_tunnel_type(room, wing_a, wing_b, triples_a, triples_b)

                    conn.execute(
                        "INSERT INTO tunnels (room_name, wing_a, wing_b, connection_type, strength, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (room, wing_a, wing_b, conn_type, 1.0, _now_iso())
                    )
                    tunnels.append({
                        "room_name": room,
                        "wing_a": wing_a,
                        "wing_b": wing_b,
                        "connection_type": conn_type,
                        "strength": 1.0,
                    })

        conn.commit()
        conn.close()
        return tunnels

    def find_tunnels_for_room(self, room_name) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT * FROM tunnels WHERE room_name = ? ORDER BY strength DESC",
            (_normalize(room_name),)
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def find_tunnels_between_wings(self, wing_a, wing_b) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT * FROM tunnels WHERE (wing_a = ? AND wing_b = ?) OR (wing_a = ? AND wing_b = ?) ORDER BY strength DESC",
            (wing_a, wing_b, wing_b, wing_a)
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def traverse_from(self, start_wing, start_room) -> Dict[str, Any]:
        visited_wings = set()
        visited_rooms = set()
        paths = []

        def _traverse(current_wing, current_room, path):
            key = (current_wing, current_room)
            if key in visited_wings and current_room == start_room:
                return
            visited_wings.add(current_wing)
            visited_rooms.add(current_room)

            tunnels = self.find_tunnels_for_room(current_room)
            for t in tunnels:
                next_wing = t["wing_b"] if t["wing_a"] == current_wing else t["wing_a"]
                if next_wing != current_wing and next_wing not in visited_wings:
                    new_path = path + [{
                        "from_wing": current_wing,
                        "room": current_room,
                        "to_wing": next_wing,
                        "connection_type": t["connection_type"],
                    }]
                    paths.append(new_path)
                    _traverse(next_wing, current_room, new_path)

        _traverse(start_wing, start_room, [])
        return {
            "wings": list(visited_wings),
            "rooms": list(visited_rooms),
            "paths": paths,
        }

    def get_tunnel_map(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM tunnels")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        adjacency = defaultdict(lambda: defaultdict(list))
        for t in rows:
            adjacency[t["wing_a"]][t["wing_b"]].append(t["room_name"])
            adjacency[t["wing_b"]][t["wing_a"]].append(t["room_name"])

        return {wing: dict(neighbors) for wing, neighbors in adjacency.items()}

    def add_tunnel(self, room_name, wing_a, wing_b, connection_type="shared_topic", strength=1.0):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO tunnels (room_name, wing_a, wing_b, connection_type, strength, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (_normalize(room_name), wing_a, wing_b, connection_type, strength, _now_iso())
        )
        conn.commit()
        conn.close()

    def remove_tunnel(self, tunnel_id):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM tunnels WHERE id = ?", (tunnel_id,))
        conn.commit()
        conn.close()

    def stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        tunnel_count = conn.execute("SELECT COUNT(*) FROM tunnels").fetchone()[0]

        room_counts = conn.execute(
            "SELECT room_name, COUNT(*) as cnt FROM tunnels GROUP BY room_name ORDER BY cnt DESC LIMIT 5"
        ).fetchall()
        most_connected_rooms = [{"room": r["room_name"], "count": r["cnt"]} for r in room_counts]

        wing_counts = conn.execute(
            "SELECT wing_a as wing, COUNT(*) as cnt FROM tunnels GROUP BY wing_a "
            "UNION ALL "
            "SELECT wing_b as wing, COUNT(*) as cnt FROM tunnels GROUP BY wing_b "
            "ORDER BY cnt DESC LIMIT 5"
        ).fetchall()
        wing_total = defaultdict(int)
        for r in wing_counts:
            wing_total[r["wing"]] += r["cnt"]
        most_connected_wings = [{"wing": w, "count": c} for w, c in
                                sorted(wing_total.items(), key=lambda x: -x[1])[:5]]

        type_breakdown = dict(conn.execute(
            "SELECT connection_type, COUNT(*) as cnt FROM tunnels GROUP BY connection_type"
        ).fetchall())

        conn.close()
        return {
            "tunnel_count": tunnel_count,
            "most_connected_rooms": most_connected_rooms,
            "most_connected_wings": most_connected_wings,
            "connection_type_breakdown": type_breakdown,
        }
