"""
Cross-Agent Memory Sync v2 - Enhanced shared memory with auto-sync triggers.

New features over v1:
- Auto-sync triggers: High-priority entries notify other agents
- Priority levels: High/Medium/Low for all shared entries
- Access pattern tracking: Track which agents access what and frequency
- Vault integration: High-priority memories auto-crystallize to vault
- Cleanup routine: Automatic expired TTL removal
- Cross-agent search: Search across all agents' shared memories
- Session traceability: Full audit trail of agent actions with context
"""

import json
import os
import time
import hashlib
from pathlib import Path
from datetime import datetime
from threading import Lock
from collections import defaultdict

SYNC_DIR = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\sync")
SYNC_DIR.mkdir(parents=True, exist_ok=True)

SHARED_MEMORY_FILE = SYNC_DIR / "shared_memory.json"
AGENT_REGISTRY_FILE = SYNC_DIR / "agent_registry.json"
SYNC_LOG_FILE = SYNC_DIR / "sync_log.json"
SESSION_TRACE_DIR = SYNC_DIR / "session_traces"
SESSION_TRACE_DIR.mkdir(parents=True, exist_ok=True)
VAULT_PATH = Path(os.environ.get("LAIS_VAULT_PATH", r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain"))

LOCK = Lock()

VALID_AGENTS = {"lais", "jarvis", "opencode", "test"}

PRIORITY_KEYWORDS = {
    "high": {
        "urgent", "critical", "important", "asap", "immediately", "priority",
        "deadline", "emergency", "fix", "bug", "error", "broken", "crash",
        "security", "vulnerability", "exploit", "breach", "current", "active",
        "now", "session", "protocol", "automated", "code", "implement", "deploy"
    },
    "medium": {
        "update", "change", "modify", "enhance", "improve", "refactor",
        "feature", "method", "approach", "technique", "specification", "insight",
        "system", "function", "class", "file", "design", "pattern", "architecture"
    }
}


def determine_priority(value, key=""):
    """Auto-determine priority based on content keywords."""
    combined = f"{key} {value}".lower()
    if any(kw in combined for kw in PRIORITY_KEYWORDS["high"]):
        return "high"
    elif any(kw in combined for kw in PRIORITY_KEYWORDS["medium"]):
        return "medium"
    return "low"


class SharedMemoryStoreV2:
    """Enhanced central shared memory accessible by all agents."""

    def __init__(self, vault_integration=True):
        self.vault_integration = vault_integration
        self.data = self._load()
        self._sync_triggers = defaultdict(list)
        self._init_sync_triggers()

    def _init_sync_triggers(self):
        """Initialize auto-sync trigger callbacks."""
        pass

    def register_sync_trigger(self, agent, callback):
        """Register a callback for when agent stores high-priority memory."""
        self._sync_triggers[agent].append(callback)

    def _load(self):
        """Load shared memory from disk, backward compatible with v1."""
        if SHARED_MEMORY_FILE.exists():
            try:
                data = json.loads(SHARED_MEMORY_FILE.read_text(encoding="utf-8"))
                if "entries" not in data:
                    data = {"entries": [], "last_sync": None, "agents": {}}
                for entry in data["entries"]:
                    if "priority" not in entry:
                        entry["priority"] = determine_priority(
                            entry.get("value", ""), entry.get("key", "")
                        )
                    if "access_patterns" not in entry:
                        entry["access_patterns"] = {}
                    if "auto_crystallized" not in entry:
                        entry["auto_crystallized"] = False
                return data
            except Exception as e:
                print(f"[MemorySyncV2] Load error: {e}")
                return {"entries": [], "last_sync": None, "agents": {}}
        return {"entries": [], "last_sync": None, "agents": {}}

    def _save(self):
        """Save shared memory to disk with lock."""
        with LOCK:
            self.data["last_sync"] = datetime.now().isoformat()
            SHARED_MEMORY_FILE.write_text(
                json.dumps(self.data, indent=2),
                encoding="utf-8"
            )

    def _notify_sync_triggers(self, agent, entry):
        """Notify registered triggers of high-priority store."""
        for callback in self._sync_triggers.get("all", []):
            try:
                callback(agent, entry)
            except Exception as e:
                pass

    def _crystallize_to_vault(self, entry):
        """Auto-crystallize high-priority entry to vault."""
        if not self.vault_integration or entry.get("auto_crystallized"):
            return
        try:
            note_title = f"Shared_{entry['agent']}_{entry['key']}"[:50]
            note_content = f"""# {note_title}

## Source
- Agent: {entry['agent']}
- Category: {entry['category']}
- Priority: {entry['priority']}
- Created: {entry['created']}

## Content
{entry['value']}

## Access Patterns
"""
            for agent_id, count in entry.get("access_patterns", {}).items():
                note_content += f"- {agent_id}: {count} accesses\n"

            note_content += f"\n## Tags\n#shared_memory #{entry['category']} #{entry['priority']}_priority\n"

            safe_title = note_title.replace(" ", "_").replace("/", "_")
            note_path = VAULT_PATH / "30_Projects" / "Shared_Memory" / f"{safe_title}.md"
            note_path.parent.mkdir(parents=True, exist_ok=True)
            note_path.write_text(note_content, encoding="utf-8")

            entry["auto_crystallized"] = True
            self._save()
        except Exception as e:
            print(f"[MemorySyncV2] Vault crystallization error: {e}")

    def store(self, agent, key, value, category="general", ttl=None, priority=None, notify=True):
        """
        Store a memory entry with enhanced features.
        - priority: explicit priority (high/medium/low) or auto-determined
        - notify: whether to trigger sync notifications
        """
        if agent not in VALID_AGENTS:
            return False

        now = datetime.now().isoformat()
        if priority is None:
            priority = determine_priority(value, key)

        entry_id = f"{agent}_{key}_{int(time.time())}"

        existing = [e for e in self.data["entries"] if e["key"] == key and e.get("agent") == agent]

        if existing:
            existing[0].update({
                "value": value,
                "updated": now,
                "ttl": ttl,
                "priority": priority
            })
            entry = existing[0]
        else:
            entry = {
                "id": entry_id,
                "agent": agent,
                "key": key,
                "value": value,
                "category": category,
                "created": now,
                "updated": now,
                "ttl": ttl,
                "priority": priority,
                "accessed_by": [agent],
                "access_patterns": {agent: 1},
                "auto_crystallized": False
            }
            self.data["entries"].append(entry)

        if agent not in self.data.get("agents", {}):
            self.data["agents"][agent] = {
                "first_seen": now,
                "last_active": now,
                "entries_stored": 0
            }
        self.data["agents"][agent]["last_active"] = now
        self.data["agents"][agent]["entries_stored"] = len(
            [e for e in self.data["entries"] if e.get("agent") == agent]
        )

        self._log_sync(agent, "store", key, priority)

        if priority == "high" and notify:
            self._notify_sync_triggers(agent, entry)

        if priority == "high" and self.vault_integration:
            self._crystallize_to_vault(entry)

        self._save()
        return True

    def retrieve(self, agent, key=None, category=None, limit=10, update_access=True):
        """
        Retrieve memories with access pattern tracking.
        - update_access: whether to update access patterns
        """
        now = time.time()
        results = []

        for entry in self.data["entries"]:
            if entry.get("ttl"):
                created_ts = datetime.fromisoformat(entry["created"]).timestamp()
                if (created_ts + entry["ttl"]) < now:
                    continue

            if key and entry["key"] != key:
                continue

            if category and entry.get("category") != category:
                continue

            if update_access:
                if "accessed_by" not in entry:
                    entry["accessed_by"] = []
                if agent not in entry["accessed_by"]:
                    entry["accessed_by"].append(agent)

                if "access_patterns" not in entry:
                    entry["access_patterns"] = {}
                entry["access_patterns"][agent] = entry["access_patterns"].get(agent, 0) + 1

            results.append(entry)

        results.sort(key=lambda x: x.get("updated", ""), reverse=True)
        if update_access and results:
            self._save()
        return results[:limit]

    def retrieve_by_agent(self, target_agent, limit=10, include_access_patterns=False):
        """Get all memories from a specific agent."""
        results = [e for e in self.data["entries"] if e.get("agent") == target_agent]
        results.sort(key=lambda x: x.get("updated", ""), reverse=True)
        return results[:limit]

    def cross_agent_search(self, query, limit=20):
        """
        Search across all agents' shared memories.
        Returns entries matching query in key, value, or category.
        """
        query_lower = query.lower()
        results = []

        for entry in self.data["entries"]:
            score = 0
            if query_lower in entry.get("key", "").lower():
                score += 3
            if query_lower in entry.get("value", "").lower():
                score += 2
            if query_lower in entry.get("category", "").lower():
                score += 1

            if score > 0:
                results.append((entry, score))

        results.sort(key=lambda x: (x[1], x[0].get("updated", "")), reverse=True)
        return [e for e, _ in results[:limit]]

    def get_access_patterns(self, entry_key=None, agent=None):
        """
        Get access pattern statistics.
        - entry_key: specific entry (None = all)
        - agent: filter by accessing agent (None = all)
        """
        patterns = {}

        for entry in self.data["entries"]:
            if entry_key and entry["key"] != entry_key:
                continue

            for agent_id, count in entry.get("access_patterns", {}).items():
                if agent and agent_id != agent:
                    continue
                if agent_id not in patterns:
                    patterns[agent_id] = {"total_accesses": 0, "entries_accessed": 0}
                patterns[agent_id]["total_accesses"] += count
                patterns[agent_id]["entries_accessed"] += 1

        return patterns

    def get_recent_updates(self, since_minutes=30, limit=20):
        """Get memories updated in the last N minutes."""
        cutoff = datetime.now().timestamp() - (since_minutes * 60)
        results = []

        for entry in self.data["entries"]:
            updated = datetime.fromisoformat(entry["updated"]).timestamp()
            if updated >= cutoff:
                results.append(entry)

        results.sort(key=lambda x: x["updated"], reverse=True)
        return results[:limit]

    def get_by_priority(self, priority, limit=20):
        """Get entries filtered by priority level."""
        results = [e for e in self.data["entries"] if e.get("priority") == priority]
        results.sort(key=lambda x: x.get("updated", ""), reverse=True)
        return results[:limit]

    def get_sync_status(self):
        """Get comprehensive sync status across all agents."""
        priority_counts = defaultdict(int)
        crystallized_count = 0

        for entry in self.data["entries"]:
            priority_counts[entry.get("priority", "low")] += 1
            if entry.get("auto_crystallized"):
                crystallized_count += 1

        return {
            "total_entries": len(self.data["entries"]),
            "agents": self.data.get("agents", {}),
            "last_sync": self.data.get("last_sync"),
            "categories": list(set(e.get("category", "general") for e in self.data["entries"])),
            "priority_counts": dict(priority_counts),
            "crystallized_to_vault": crystallized_count,
            "access_patterns": self.get_access_patterns()
        }

    def cleanup_expired(self):
        """Remove expired TTL entries and return count removed."""
        now = time.time()
        original_count = len(self.data["entries"])

        self.data["entries"] = [
            e for e in self.data["entries"]
            if not e.get("ttl") or (
                datetime.fromisoformat(e["created"]).timestamp() + e["ttl"]
            ) >= now
        ]

        removed = original_count - len(self.data["entries"])
        if removed > 0:
            self._save()
        return removed

    def _log_sync(self, agent, action, key, priority="low"):
        """Log sync action with priority."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "key": key,
            "priority": priority
        }

        try:
            if SYNC_LOG_FILE.exists():
                log = json.loads(SYNC_LOG_FILE.read_text(encoding="utf-8"))
            else:
                log = []

            log.append(log_entry)
            SYNC_LOG_FILE.write_text(json.dumps(log[-200:], indent=2), encoding="utf-8")
        except Exception as e:
            pass

    def get_agent_activity(self, agent):
        entries = [e for e in self.data["entries"] if e.get("agent") == agent]
        accessed = [e for e in self.data["entries"] if agent in e.get("accessed_by", [])]

        return {
            "agent": agent,
            "entries_created": len(entries),
            "entries_accessed": len(accessed),
            "last_active": self.data.get("agents", {}).get(agent, {}).get("last_active"),
            "priority_breakdown": {
                p: len([e for e in entries if e.get("priority") == p])
                for p in ["high", "medium", "low"]
            }
        }

    def log_session_action(self, agent, action, context=None, metadata=None):
        action_hash = hashlib.md5(f"{agent}{action}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        trace_entry = {
            "trace_id": f"trace_{action_hash}",
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "context": context or {},
            "metadata": metadata or {}
        }
        agent_trace_file = SESSION_TRACE_DIR / f"{agent}_trace.json"
        try:
            if agent_trace_file.exists():
                traces = json.loads(agent_trace_file.read_text(encoding="utf-8"))
            else:
                traces = []
            traces.append(trace_entry)
            agent_trace_file.write_text(json.dumps(traces[-500:], indent=2), encoding="utf-8")
        except Exception:
            pass
        return trace_entry["trace_id"]

    def get_session_trace(self, agent, limit=20):
        agent_trace_file = SESSION_TRACE_DIR / f"{agent}_trace.json"
        if agent_trace_file.exists():
            try:
                traces = json.loads(agent_trace_file.read_text(encoding="utf-8"))
                return traces[-limit:]
            except Exception:
                return []
        return []

    def get_cross_agent_trace(self, limit=50):
        all_traces = []
        for trace_file in SESSION_TRACE_DIR.glob("*_trace.json"):
            try:
                traces = json.loads(trace_file.read_text(encoding="utf-8"))
                all_traces.extend(traces)
            except Exception:
                continue
        all_traces.sort(key=lambda x: x.get("timestamp", ""))
        return all_traces[-limit:]


def load_shared_memory_v2(vault_integration=True):
    """Factory function for v2 store."""
    return SharedMemoryStoreV2(vault_integration=vault_integration)


if __name__ == "__main__":
    store = load_shared_memory_v2()

    print("=== Cross-Agent Memory Sync v2 ===")
    status = store.get_sync_status()
    print(f"Total entries: {status['total_entries']}")
    print(f"Agents: {list(status['agents'].keys())}")
    print(f"Priority counts: {status['priority_counts']}")
    print(f"Crystallized to vault: {status['crystallized_to_vault']}")

    print("\n=== Test: Store with Priority ===")
    store.store("lais", "urgent_fix", "Critical security patch needed", "alert", priority="high")
    store.store("jarvis", "meeting_note", "Discussed project timeline", "context", priority="medium")
    store.store("opencode", "code_ref", "Use pattern X for Y", "reference", priority="low")

    print("\n=== Test: Cross-Agent Search ===")
    results = store.cross_agent_search("project")
    for r in results:
        print(f"  [{r['agent']}/{r['priority']}] {r['key']}: {r['value'][:50]}")

    print("\n=== Access Patterns ===")
    patterns = store.get_access_patterns()
    for agent, stats in patterns.items():
        print(f"  {agent}: {stats['total_accesses']} accesses across {stats['entries_accessed']} entries")

    print("\n=== Cleanup ===")
    removed = store.cleanup_expired()
    print(f"Removed {removed} expired entries")
