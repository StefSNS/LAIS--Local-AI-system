"""
Unified Search - Hybrid search combining SQLite (FTS5 + vector) with existing embeddings
Single interface for all agents to search memories, conversations, skills, and vault notes.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import sys
from pathlib import Path

TXTAI_AVAILABLE = False
try:
    from ..plugins.semantic_search import TxtaiSearch, load_txtai_search
    TXTAI_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    try:
        from plugins.semantic_search import TxtaiSearch, load_txtai_search
        TXTAI_AVAILABLE = True
    except (ImportError, ModuleNotFoundError):
        pass

try:
    from .memory_sqlite import SQLiteMemory, load_sqlite_memory
    from .embeddings import EmbeddingSearch, load_embedding_search, semantic_search
except ImportError:
    omnis_path = str(Path(__file__).resolve().parent.parent)
    if omnis_path not in sys.path:
        sys.path.insert(0, omnis_path)
    from unified_layer.memory_sqlite import SQLiteMemory, load_sqlite_memory
    from unified_layer.embeddings import EmbeddingSearch, load_embedding_search, semantic_search


class UnifiedSearch:
    """
    Hybrid search that queries:
    1. SQLite memory (FTS5 + vector) - fast, structured
    2. Vault embeddings (sentence-transformers) - semantic vault search
    3. Combined ranking for best results
    """

    def __init__(self):
        self.sqlite = load_sqlite_memory()
        self.vault_search = load_embedding_search()
        self.txtai = load_txtai_search() if TXTAI_AVAILABLE else None
        if self.txtai:
            print("[UnifiedSearch] Txtai semantic search enabled")
        else:
            print("[UnifiedSearch] Txtai not available, using SQLite FTS5 only")

    def search_all(
        self,
        query: str,
        max_results_per_source: int = 5,
        sources: Optional[List[str]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across all sources. Returns results grouped by source.

        Args:
            query: Search query
            max_results_per_source: Max results per source
            sources: Which sources to search (default: all)
                     Options: 'memory', 'conversations', 'skills', 'vault'
        """
        if sources is None:
            sources = ["memory", "conversations", "skills", "vault", "semantic"]

        results = {}

        if "memory" in sources:
            results["memory"] = self.sqlite.search_memory(
                query, max_results=max_results_per_source
            )

        if "conversations" in sources:
            results["conversations"] = self.sqlite.search_conversations(
                query, max_results=max_results_per_source
            )

        if "skills" in sources:
            results["skills"] = self.sqlite.search_skills(
                query, max_results=max_results_per_source
            )

        if "vault" in sources:
            vault_results = self.vault_search.search(query, max_results=max_results_per_source)
            results["vault"] = vault_results

        if "semantic" in sources and self.txtai:
            results["semantic"] = self.txtai.search(query, max_results=max_results_per_source)
        elif "semantic" in sources:
            results["semantic"] = []

        return results

    def search_with_context(
        self,
        query: str,
        max_results: int = 5,
    ) -> str:
        """
        Search all sources and return formatted context string for LLM injection.
        This is what agents should use when they need background knowledge.
        """
        all_results = self.search_all(query, max_results_per_source=3)

        context_parts = []

        # Memories
        if all_results.get("memory"):
            context_parts.append("## Relevant Memories")
            for m in all_results["memory"][:3]:
                context_parts.append(f"- [{m['category']}] {m['key']}: {m['value'][:150]}")

        # Conversations
        if all_results.get("conversations"):
            context_parts.append("## Past Conversations")
            for c in all_results["conversations"][:3]:
                context_parts.append(
                    f"- [{c['agent']}] {c['role']}: {c['content'][:150]}"
                )

        # Skills
        if all_results.get("skills"):
            context_parts.append("## Available Skills")
            for s in all_results["skills"][:3]:
                context_parts.append(
                    f"- {s['name']}: {s['description']} (used {s['usage_count']} times)"
                )

        # Vault notes
        if all_results.get("vault"):
            context_parts.append("## Vault Notes")
            for v in all_results["vault"][:3]:
                context_parts.append(
                    f"- [{v['score']:.3f}] {v['title']}: {v['content'][:150]}..."
                )

        # Semantic search results
        if all_results.get("semantic"):
            context_parts.append("## Semantic Results")
            for s in all_results["semantic"][:3]:
                context_parts.append(
                    f"- [{s['score']:.3f}] {s['title']}: {s['text'][:150]}..."
                )

        return "\n".join(context_parts) if context_parts else "No relevant context found."

    def get_agent_context(
        self,
        agent: str,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Get context specific to an agent (recent memories + conversations).
        Used at session start to prime the agent.
        """
        parts = []

        # Recent memories from this agent
        memories = self.sqlite.get_memories_by_agent(agent, limit=10)
        if memories:
            parts.append(f"## {agent.title()} Recent Memories")
            for m in memories[:5]:
                parts.append(f"- [{m['category']}] {m['key']}: {m['value'][:100]}")

        # Recent conversations
        convs = self.sqlite.get_recent_conversations(
            agent=agent, session_id=session_id, limit=20
        )
        if convs:
            parts.append(f"## Recent Conversation ({len(convs)} turns)")
            for c in convs[-10:]:
                role = c["role"].upper()
                parts.append(f"{role}: {c['content'][:100]}")

        return "\n".join(parts) if parts else f"No context found for {agent}."

    def rebuild(self):
        """Rebuild vault embeddings and txtai index (call after vault changes)."""
        self.vault_search.rebuild()
        if self.txtai:
            self.txtai.rebuild()

    def get_stats(self) -> Dict[str, Any]:
        """Get combined statistics."""
        sqlite_stats = self.sqlite.get_stats()
        vault_stats = self.vault_search.get_stats()

        stats = {
            "sqlite": sqlite_stats,
            "vault": vault_stats,
            "txtai": self.txtai.get_stats() if self.txtai else {"available": False},
        }

        return stats

    def close(self):
        """Clean up resources."""
        self.sqlite.close()


def load_unified_search() -> UnifiedSearch:
    """Factory function."""
    return UnifiedSearch()


if __name__ == "__main__":
    import sys
    import importlib.util
    
    omnis_path = r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis"
    if omnis_path not in sys.path:
        sys.path.insert(0, omnis_path)
    
    # Load modules directly by path
    mem_spec = importlib.util.spec_from_file_location(
        "memory_sqlite",
        Path(omnis_path) / "unified_layer" / "memory_sqlite.py"
    )
    mem_mod = importlib.util.module_from_spec(mem_spec)
    mem_spec.loader.exec_module(mem_mod)
    load_sqlite_memory = mem_mod.load_sqlite_memory
    
    emb_spec = importlib.util.spec_from_file_location(
        "embeddings",
        Path(omnis_path) / "unified_layer" / "embeddings.py"
    )
    emb_mod = importlib.util.module_from_spec(emb_spec)
    emb_spec.loader.exec_module(emb_mod)
    load_embedding_search = emb_mod.load_embedding_search

    search = load_unified_search()

    print("=== Unified Search ===")
    stats = search.get_stats()
    print(f"SQLite: {stats['sqlite']['memory_entries']} memories, "
          f"{stats['sqlite']['conversations']} conversations, "
          f"{stats['sqlite']['skills']} skills")
    print(f"Vault: {stats['vault']['notes_indexed']} notes indexed")
    print(f"DB size: {stats['sqlite']['db_size_mb']}MB")

    print("\n=== Test: Search All ===")
    results = search.search_all("user preferences", max_results_per_source=3)
    for source, items in results.items():
        if items:
            print(f"\n  {source} ({len(items)} results):")
            for item in items[:2]:
                content = item.get("value", item.get("content", item.get("title", "")))
                print(f"    - {content[:80]}...")

    print("\n=== Test: Context for LLM ===")
    context = search.search_with_context("architecture evolution")
    print(context)

    print("\n=== Test: Agent Context ===")
    agent_ctx = search.get_agent_context("opencode")
    print(agent_ctx)

    search.close()
