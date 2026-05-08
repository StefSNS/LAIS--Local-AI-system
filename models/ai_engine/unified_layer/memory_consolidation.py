"""
Memory Consolidation v1.0 - Sleep cycle for long-term memory.
Compresses short-term memories into long-term vault entries.
Prevents context bloat and enables persistent learning.
Pattern: Collect â†’ Cluster â†’ Summarize â†’ Store â†’ Prune
"""

import json
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from threading import Lock


MEMORY_DIR = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge\memory")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
SHORT_TERM_FILE = MEMORY_DIR / "short_term.json"
CONSOLIDATED_FILE = MEMORY_DIR / "consolidated.json"
CONSOLIDATION_LOG = MEMORY_DIR / "consolidation_log.json"


class MemoryItem:
    """A single memory entry."""

    def __init__(
        self,
        content: str,
        category: str = "general",
        importance: float = 0.5,
        access_count: int = 0,
        created_at: Optional[datetime] = None,
        last_accessed: Optional[datetime] = None,
    ):
        self.content = content
        self.category = category
        self.importance = importance
        self.access_count = access_count
        self.created_at = created_at or datetime.now()
        self.last_accessed = last_accessed or datetime.now()

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "category": self.category,
            "importance": round(self.importance, 3),
            "access_count": self.access_count,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryItem":
        return cls(
            content=data["content"],
            category=data.get("category", "general"),
            importance=data.get("importance", 0.5),
            access_count=data.get("access_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if "last_accessed" in data else None,
        )


class ShortTermMemory:
    """RAM-resident short-term memory with persistence."""

    def __init__(self, filepath: Path = SHORT_TERM_FILE, max_items: int = 200):
        self.filepath = filepath
        self.max_items = max_items
        self._items = []
        self._lock = Lock()
        self._load()

    def add(self, content: str, category: str = "general", importance: float = 0.5) -> None:
        with self._lock:
            item = MemoryItem(content, category, importance)
            self._items.append(item)
            if len(self._items) > self.max_items:
                self._prune_low_priority()
            self._save()

    def get_all(self) -> list[MemoryItem]:
        return list(self._items)

    def get_by_category(self, category: str) -> list[MemoryItem]:
        return [i for i in self._items if i.category == category]

    def access(self, index: int) -> Optional[MemoryItem]:
        if 0 <= index < len(self._items):
            self._items[index].access_count += 1
            self._items[index].last_accessed = datetime.now()
            return self._items[index]
        return None

    def clear(self) -> int:
        count = len(self._items)
        self._items.clear()
        self._save()
        return count

    def count(self) -> int:
        return len(self._items)

    def _prune_low_priority(self) -> None:
        self._items.sort(key=lambda x: (x.access_count, x.importance))
        remove_count = len(self._items) - self.max_items
        if remove_count > 0:
            self._items = self._items[remove_count:]

    def _load(self) -> None:
        if self.filepath.exists():
            try:
                data = json.loads(self.filepath.read_text(encoding="utf-8"))
                self._items = [MemoryItem.from_dict(d) for d in data]
            except Exception:
                self._items = []

    def _save(self) -> None:
        data = [i.to_dict() for i in self._items]
        self.filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")


class ConsolidatedMemory:
    """Long-term memory store for consolidated insights."""

    def __init__(self, filepath: Path = CONSOLIDATED_FILE):
        self.filepath = filepath
        self._entries = {}
        self._lock = Lock()
        self._load()

    def store(self, key: str, content: str, category: str = "general", tags: list[str] = None) -> None:
        with self._lock:
            self._entries[key] = {
                "content": content,
                "category": category,
                "tags": tags or [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            self._save()

    def get(self, key: str) -> Optional[dict]:
        return self._entries.get(key)

    def get_by_category(self, category: str) -> dict:
        return {k: v for k, v in self._entries.items() if v.get("category") == category}

    def get_all(self) -> dict:
        return dict(self._entries)

    def search(self, query: str) -> list[dict]:
        results = []
        query_lower = query.lower()
        for key, entry in self._entries.items():
            score = 0
            if query_lower in entry["content"].lower():
                score += 3
            if query_lower in entry.get("category", "").lower():
                score += 2
            if any(query_lower in tag.lower() for tag in entry.get("tags", [])):
                score += 1
            if score > 0:
                results.append({"key": key, "score": score, **entry})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def remove(self, key: str) -> bool:
        with self._lock:
            if key in self._entries:
                del self._entries[key]
                self._save()
                return True
        return False

    def count(self) -> int:
        return len(self._entries)

    def _load(self) -> None:
        if self.filepath.exists():
            try:
                self._entries = json.loads(self.filepath.read_text(encoding="utf-8"))
            except Exception:
                self._entries = {}

    def _save(self) -> None:
        self.filepath.write_text(json.dumps(self._entries, indent=2), encoding="utf-8")


class MemoryConsolidator:
    """
    Runs the consolidation cycle:
    1. Collect short-term memories
    2. Cluster by topic/category
    3. Summarize clusters into insights
    4. Store in long-term memory
    5. Prune redundant short-term items
    """

    def __init__(
        self,
        short_term: Optional[ShortTermMemory] = None,
        consolidated: Optional[ConsolidatedMemory] = None,
    ):
        self.short_term = short_term or ShortTermMemory()
        self.consolidated = consolidated or ConsolidatedMemory()
        self._log_path = CONSOLIDATION_LOG
        self._consolidation_history = self._load_log()

    def run_consolidation(self, transport_chat_fn=None) -> dict:
        """Execute full consolidation cycle."""
        items = self.short_term.get_all()
        if not items:
            return {"status": "skipped", "reason": "No short-term memories"}

        clusters = self._cluster_by_topic(items)
        summaries = {}

        for topic, cluster_items in clusters.items():
            if len(cluster_items) < 2:
                continue

            combined = "\n".join(i.content for i in cluster_items[:10])
            summary = self._summarize_cluster(combined, topic, transport_chat_fn)
            key = f"{topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            tags = self._extract_tags(cluster_items)
            self.consolidated.store(
                key=key,
                content=summary,
                category=topic,
                tags=tags,
            )
            summaries[key] = summary

        self._write_to_vault(summaries)
        removed = self._prune_consolidated(items)

        result = {
            "status": "completed",
            "items_processed": len(items),
            "clusters_found": len(clusters),
            "summaries_created": len(summaries),
            "items_pruned": removed,
            "timestamp": datetime.now().isoformat(),
        }

        self._consolidation_history.append(result)
        self._save_log()

        return result

    def add_short_term(self, content: str, category: str = "general", importance: float = 0.5) -> None:
        """Add a memory to short-term storage."""
        self.short_term.add(content, category, importance)

    def recall(self, query: str) -> list[dict]:
        """Search both short-term and consolidated memory."""
        results = []

        for item in self.short_term.get_all():
            if query.lower() in item.content.lower():
                results.append({
                    "source": "short_term",
                    "content": item.content,
                    "relevance": item.importance,
                })

        consolidated_results = self.consolidated.search(query)
        for r in consolidated_results:
            results.append({
                "source": "consolidated",
                "content": r["content"],
                "relevance": r["score"] / 3.0,
            })

        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:10]

    def get_stats(self) -> dict:
        return {
            "short_term_count": self.short_term.count(),
            "consolidated_count": self.consolidated.count(),
            "consolidations_run": len(self._consolidation_history),
            "last_consolidation": self._consolidation_history[-1]["timestamp"] if self._consolidation_history else None,
        }

    def _cluster_by_topic(self, items: list[MemoryItem]) -> dict[str, list[MemoryItem]]:
        clusters = {}
        for item in items:
            topic = item.category
            if topic not in clusters:
                clusters[topic] = []
            clusters[topic].append(item)

        return {k: v for k, v in clusters.items() if len(v) >= 1}

    def _summarize_cluster(
        self,
        combined_content: str,
        topic: str,
        transport_chat_fn=None,
    ) -> str:
        if transport_chat_fn:
            prompt = f"""Condense these related memories about {topic} into a single, clear insight.
Focus on key facts, decisions, and patterns. Remove redundancy.

Memories:
{combined_content[:2000]}

Consolidated insight (3-5 sentences):"""

            try:
                result = transport_chat_fn(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=300,
                )
                summary = result.get("text", "").strip()
                if summary:
                    return summary
            except Exception:
                pass

        return combined_content[:500]

    def _extract_tags(self, items: list[MemoryItem]) -> list[str]:
        all_text = " ".join(i.content.lower() for i in items)
        words = re.findall(r'\b[a-z]{4,}\b', all_text)
        stop_words = {"this", "that", "with", "from", "have", "been", "will", "would", "should"}
        counter = Counter(w for w in words if w not in stop_words)
        return [word for word, _ in counter.most_common(5)]

    def _write_to_vault(self, summaries: dict) -> None:
        vault_dir = Path(os.environ.get("LAIS_VAULT_PATH", r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain")) / "20_Memory"
        vault_dir.mkdir(parents=True, exist_ok=True)

        for key, content in summaries.items():
            filepath = vault_dir / f"{key}.md"
            if not filepath.exists():
                content_md = f"""---
created: {datetime.now().isoformat()}
tags: [consolidated, memory]
---

# Consolidated Memory: {key}

{content}

---
*Auto-generated by memory consolidation cycle*
"""
                filepath.write_text(content_md, encoding="utf-8")

    def _prune_consolidated(self, items: list[MemoryItem]) -> int:
        to_remove = [i for i in items if i.access_count == 0 and i.importance < 0.3]
        for item in to_remove:
            if item in items:
                items.remove(item)
        self.short_term._save()
        return len(to_remove)

    def _load_log(self) -> list:
        if self._log_path.exists():
            try:
                return json.loads(self._log_path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_log(self) -> None:
        self._log_path.write_text(json.dumps(self._consolidation_history, indent=2), encoding="utf-8")


_global_consolidator: Optional[MemoryConsolidator] = None
_consolidator_lock = Lock()


def get_consolidator() -> MemoryConsolidator:
    global _global_consolidator
    if _global_consolidator is None:
        with _consolidator_lock:
            if _global_consolidator is None:
                _global_consolidator = MemoryConsolidator()
    return _global_consolidator
