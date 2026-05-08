"""
DuckDB Analytics Engine - Local SQL analytics layer for memory and vault data.
Handles analytical queries (aggregations, trends, cross-source joins) that
SQLiteMemory's operational queries aren't optimized for.

RAM footprint: ~50MB (DuckDB in-memory)
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import duckdb

MEMORY_DB_PATH = Path(
    r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\unified_memory.db"
)
ANALYTICS_DB_PATH = Path(
    r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\analytics.db"
)
ANALYTICS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class AnalyticsEngine:
    """
    DuckDB-powered analytics layer.
    - Reads from SQLite memory database via DuckDB's SQLite reader
    - Supports analytical queries: trends, aggregations, patterns
    - Can query vault markdown files as a table
    - Materialized views for fast repeated queries
    """

    def __init__(self, memory_db: Optional[Path] = None, analytics_db: Optional[Path] = None):
        self.memory_db = memory_db or MEMORY_DB_PATH
        self.analytics_db = analytics_db or ANALYTICS_DB_PATH
        self.conn = duckdb.connect(str(self.analytics_db))
        self._register_sources()

    def _register_sources(self):
        """Register external data sources as DuckDB tables."""
        # Read from SQLite memory database
        if self.memory_db.exists():
            self.conn.execute(
                f"""
                CREATE OR REPLACE VIEW memory_entries AS
                SELECT * FROM sqlite_scan('{self.memory_db}', 'memory_entries')
                """
            )
            self.conn.execute(
                f"""
                CREATE OR REPLACE VIEW conversations AS
                SELECT * FROM sqlite_scan('{self.memory_db}', 'conversations')
                """
            )
            self.conn.execute(
                f"""
                CREATE OR REPLACE VIEW skills AS
                SELECT * FROM sqlite_scan('{self.memory_db}', 'skills')
                """
            )
            print("[AnalyticsEngine] SQLite memory sources registered")
        else:
            # Create empty tables for standalone mode
            self.conn.execute("""
                CREATE OR REPLACE TABLE memory_entries (
                    id INTEGER, agent VARCHAR, key VARCHAR, value VARCHAR,
                    category VARCHAR, created VARCHAR, updated VARCHAR,
                    ttl INTEGER
                )
            """)
            self.conn.execute("""
                CREATE OR REPLACE TABLE conversations (
                    id INTEGER, agent VARCHAR, session_id VARCHAR,
                    role VARCHAR, content VARCHAR, timestamp VARCHAR
                )
            """)
            print("[AnalyticsEngine] Using standalone mode (no SQLite source)")

    def query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute an analytical SQL query."""
        try:
            result = self.conn.execute(sql).fetchall()
            columns = [desc[0] for desc in self.conn.description]
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            return [{"error": str(e)}]

    def agent_activity_summary(self, agent: str) -> Dict[str, Any]:
        """Get activity summary for a specific agent."""
        results = self.query(f"""
            SELECT
                COUNT(*) as total_memories,
                COUNT(DISTINCT category) as categories_used,
                MIN(created) as first_memory,
                MAX(updated) as last_updated
            FROM memory_entries
            WHERE agent = '{agent}'
        """)

        conv_results = self.query(f"""
            SELECT
                COUNT(*) as total_turns,
                COUNT(DISTINCT session_id) as sessions
            FROM conversations
            WHERE agent = '{agent}'
        """)

        skill_results = self.query(f"""
            SELECT COUNT(*) as total_skills
            FROM skills
        """)

        return {
            "agent": agent,
            "memories": results[0] if results else {},
            "conversations": conv_results[0] if conv_results else {},
            "skills": skill_results[0] if skill_results else {},
        }

    def category_distribution(self) -> List[Dict[str, Any]]:
        """Get memory distribution by category."""
        return self.query("""
            SELECT category, COUNT(*) as count
            FROM memory_entries
            GROUP BY category
            ORDER BY count DESC
        """)

    def conversation_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get conversation volume over the last N days."""
        return self.query(f"""
            SELECT
                DATE(timestamp) as day,
                COUNT(*) as turns,
                COUNT(DISTINCT agent) as active_agents,
                COUNT(DISTINCT session_id) as sessions
            FROM conversations
            WHERE timestamp >= DATE('now', '-{days} days')
            GROUP BY DATE(timestamp)
            ORDER BY day DESC
        """)

    def top_memory_keys(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Find the most frequently referenced memory keys."""
        return self.query(f"""
            SELECT key, COUNT(*) as occurrences, COUNT(DISTINCT agent) as agents
            FROM memory_entries
            GROUP BY key
            ORDER BY occurrences DESC
            LIMIT {limit}
        """)

    def agent_comparison(self) -> List[Dict[str, Any]]:
        """Compare activity across all agents."""
        return self.query("""
            SELECT
                agent,
                COUNT(*) as memories,
                COUNT(DISTINCT category) as categories
            FROM memory_entries
            GROUP BY agent
            ORDER BY memories DESC
        """)

    def vault_file_stats(self, vault_path: Optional[Path] = None) -> Dict[str, Any]:
        """Get statistics about vault files."""
        vault_path = vault_path or Path(r"str(Path(__file__).resolve().parent.parent)\knowledge")

        if not vault_path.exists():
            return {"error": "Vault path not found"}

        total_files = 0
        total_size = 0
        by_extension = {}
        by_subdir = {}

        for root, dirs, files in os.walk(vault_path):
            rel = Path(root).relative_to(vault_path)
            subdir = str(rel) if str(rel) != "." else "root"
            by_subdir[subdir] = by_subdir.get(subdir, 0) + len(files)

            for f in files:
                ext = Path(f).suffix.lower()
                by_extension[ext] = by_extension.get(ext, 0) + 1
                total_files += 1
                total_size += (Path(root) / f).stat().st_size

        return {
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_extension": by_extension,
            "by_subdir": by_subdir,
        }

    def search_analytics(self, query_text: str) -> List[Dict[str, Any]]:
        """Search memories using DuckDB's full-text capabilities."""
        # DuckDB can do FTS via regexp or similarity
        return self.query(f"""
            SELECT key, value, category, agent, created,
                   length(value) as value_length
            FROM memory_entries
            WHERE value ILIKE '%{query_text}%'
               OR key ILIKE '%{query_text}%'
            ORDER BY length(value) DESC
            LIMIT 20
        """)

    def export_report(self, output_path: Optional[Path] = None) -> str:
        """Generate a comprehensive analytics report."""
        output_path = output_path or Path(
            r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\analytics_report.json"
        )

        report = {
            "generated_at": datetime.now().isoformat(),
            "agent_activity": {},
            "category_distribution": self.category_distribution(),
            "conversation_trends_7d": self.conversation_trends(7),
            "top_memory_keys": self.top_memory_keys(),
            "agent_comparison": self.agent_comparison(),
        }

        # Get activity for each agent
        agents = self.agent_comparison()
        for agent_data in agents:
            agent_name = agent_data.get("agent", "unknown")
            report["agent_activity"][agent_name] = self.agent_activity_summary(agent_name)

        output_path.write_text(json.dumps(report, indent=2, default=str))
        return str(output_path)

    def close(self):
        """Close DuckDB connection."""
        self.conn.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


import os

def load_analytics_engine(memory_db=None, analytics_db=None) -> AnalyticsEngine:
    """Factory function."""
    return AnalyticsEngine(memory_db, analytics_db)


if __name__ == "__main__":
    print("=== DuckDB Analytics Engine ===")
    engine = load_analytics_engine()

    print("\n--- Agent Activity (opencode) ---")
    summary = engine.agent_activity_summary("opencode")
    print(json.dumps(summary, indent=2, default=str))

    print("\n--- Category Distribution ---")
    cats = engine.category_distribution()
    for c in cats:
        print(f"  {c['category']}: {c['count']}")

    print("\n--- Agent Comparison ---")
    agents = engine.agent_comparison()
    for a in agents:
        print(f"  {a['agent']}: {a['memories']} memories, {a['categories']} categories")

    print("\n--- Vault Stats ---")
    vault = engine.vault_file_stats()
    print(f"  Files: {vault['total_files']}")
    print(f"  Size: {vault['total_size_mb']}MB")
    print(f"  Extensions: {vault['by_extension']}")

    print("\n--- Export Report ---")
    report_path = engine.export_report()
    print(f"  Report saved to: {report_path}")

    engine.close()
