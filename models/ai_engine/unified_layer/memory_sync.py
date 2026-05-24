"""
Cross-Agent Memory Sync - Shared memory between LAIS, Jarvis, and OpenCode
All agents read/write to a common store with timestamps and attribution.
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
from threading import Lock

SYNC_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "memory" / "sync"
SYNC_DIR.mkdir(parents=True, exist_ok=True)

SHARED_MEMORY_FILE = SYNC_DIR / "shared_memory.json"
AGENT_REGISTRY_FILE = SYNC_DIR / "agent_registry.json"
SYNC_LOG_FILE = SYNC_DIR / "sync_log.json"
LOCK = Lock()

VALID_AGENTS = {"lais", "jarvis", "opencode", "test"}


class SharedMemoryStore:
    """Central shared memory accessible by all agents."""
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self):
        """Load shared memory from disk."""
        if SHARED_MEMORY_FILE.exists():
            try:
                return json.loads(SHARED_MEMORY_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                return {"entries": [], "last_sync": None, "agents": {}}
        return {"entries": [], "last_sync": None, "agents": {}}
    
    def _save(self):
        """Save shared memory to disk."""
        with LOCK:
            self.data["last_sync"] = datetime.now().isoformat()
            SHARED_MEMORY_FILE.write_text(
                json.dumps(self.data, indent=2),
                encoding="utf-8"
            )
    
    def store(self, agent, key, value, category="general", ttl=None):
        """
        Store a memory entry.
        agent: which agent is storing this (lais/jarvis/opencode)
        key: unique identifier for this memory
        value: the actual content
        category: type of memory (preference/fact/project/context/insight)
        ttl: time-to-live in seconds (None = permanent)
        """
        if agent not in VALID_AGENTS:
            return False
        
        now = datetime.now().isoformat()
        entry = {
            "id": f"{agent}_{key}_{int(time.time())}",
            "agent": agent,
            "key": key,
            "value": value,
            "category": category,
            "created": now,
            "updated": now,
            "ttl": ttl,
            "accessed_by": [agent]
        }
        
        existing = [e for e in self.data["entries"] if e["key"] == key and e.get("agent") == agent]
        if existing:
            existing[0].update({
                "value": value,
                "updated": now,
                "ttl": ttl
            })
        else:
            self.data["entries"].append(entry)
        
        if agent not in self.data.get("agents", {}):
            self.data["agents"][agent] = {
                "first_seen": now,
                "last_active": now,
                "entries_stored": 0
            }
        self.data["agents"][agent]["last_active"] = now
        self.data["agents"][agent]["entries_stored"] += 1
        
        self._log_sync(agent, "store", key)
        self._save()
        return True
    
    def retrieve(self, agent, key=None, category=None, limit=10):
        """
        Retrieve memories.
        agent: requesting agent
        key: specific key to look up (optional)
        category: filter by category (optional)
        limit: max results
        """
        now = time.time()
        results = []
        
        for entry in self.data["entries"]:
            if entry.get("ttl") and (datetime.fromisoformat(entry["created"]).timestamp() + entry["ttl"]) < now:
                continue
            
            if key and entry["key"] != key:
                continue
            
            if category and entry.get("category") != category:
                continue
            
            if "accessed_by" not in entry:
                entry["accessed_by"] = []
            if agent not in entry["accessed_by"]:
                entry["accessed_by"].append(agent)
            
            results.append(entry)
        
        results.sort(key=lambda x: x.get("updated", ""), reverse=True)
        return results[:limit]
    
    def retrieve_by_agent(self, target_agent, limit=10):
        """Get all memories from a specific agent."""
        results = [e for e in self.data["entries"] if e.get("agent") == target_agent]
        results.sort(key=lambda x: x.get("updated", ""), reverse=True)
        return results[:limit]
    
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
    
    def get_sync_status(self):
        """Get sync status across all agents."""
        return {
            "total_entries": len(self.data["entries"]),
            "agents": self.data.get("agents", {}),
            "last_sync": self.data.get("last_sync"),
            "categories": list(set(e.get("category", "general") for e in self.data["entries"]))
        }
    
    def cleanup_expired(self):
        """Remove expired TTL entries."""
        now = time.time()
        original_count = len(self.data["entries"])
        self.data["entries"] = [
            e for e in self.data["entries"]
            if not e.get("ttl") or (datetime.fromisoformat(e["created"]).timestamp() + e["ttl"]) >= now
        ]
        removed = original_count - len(self.data["entries"])
        if removed > 0:
            self._save()
        return removed
    
    def _log_sync(self, agent, action, key):
        """Log sync action."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "key": key
        }
        
        try:
            if SYNC_LOG_FILE.exists():
                log = json.loads(SYNC_LOG_FILE.read_text(encoding="utf-8"))
            else:
                log = []
            
            log.append(log_entry)
            SYNC_LOG_FILE.write_text(json.dumps(log[-100:], indent=2), encoding="utf-8")
        except Exception as e:
            pass


def load_shared_memory():
    """Factory function."""
    return SharedMemoryStore()


if __name__ == "__main__":
    store = load_shared_memory()
    
    print("=== Cross-Agent Memory Sync ===")
    status = store.get_sync_status()
    print(f"Total entries: {status['total_entries']}")
    print(f"Agents: {list(status['agents'].keys())}")
    print(f"Categories: {status['categories']}")
    
    print("\n=== Test: Store Memories ===")
    store.store("lais", "user_pref_theme", "User prefers dark mode", "preference")
    store.store("jarvis", "user_schedule", "User has meeting at 3pm", "context")
    store.store("opencode", "project_status", "Unified layer complete", "project")
    
    print("\n=== Test: Retrieve ===")
    all_memories = store.retrieve("test", limit=5)
    for m in all_memories:
        print(f"  [{m['agent']}] {m['key']}: {m['value'][:50]}")
    
    print("\n=== Test: Recent Updates ===")
    recent = store.get_recent_updates(since_minutes=5)
    for r in recent:
        print(f"  [{r['agent']}] {r['key']}: {r['updated']}")
