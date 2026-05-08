"""
Unified Memory System v2.0 - Consolidated
Combines best of unified_memory.py and continuity_manager.py
Now includes: RAG, auto-compression, cross-session learning, agent registry
"""

import json
import os
import sys
from datetime import datetime
from threading import Lock
from pathlib import Path
from collections import Counter
import re

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEMORY_DIR = Path(__file__).resolve().parent
SESSIONS_DIR = MEMORY_DIR / "sessions"
KNOWLEDGE_BASE = BASE_DIR / "knowledge" / "base"

MEMORY_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

MEMORY_FILE = MEMORY_DIR / "long_term.json"
CRYSTALLIZED_FILE = MEMORY_DIR / "crystallized.json"
CRYSTALLIZED_ALT = MEMORY_DIR / "crystallized_knowledge.json"
REGISTRY_FILE = MEMORY_DIR / "agent_registry.json"
LOCK = Lock()

# Relevance keywords (from both systems)
HIGH_KEYWORDS = {
    "current", "active", "now", "working", "focus", "session", "continuity",
    "protocol", "automated", "code", "fix", "bug", "error", "implement",
    "create", "lais", "ai", "project", "task", "urgent", "priority"
}
MEDIUM_KEYWORDS = {
    "method", "approach", "technique", "specification", "insight",
    "system", "function", "class", "file", "design", "pattern", "architecture"
}
LOW_KEYWORDS = {
    "background", "history", "archive", "example", "test", "demo",
    "old", "previous", "yesterday", "obsolete"
}

# Skill usage tracking
SKILL_USAGE_FILE = MEMORY_DIR / "skill_usage.json"


def _empty_memory():
    return {
        "identity": {},
        "preferences": {},
        "projects": {},
        "relationships": {},
        "wishes": {},
        "notes": {},
        "session_history": {}
    }


class UnifiedMemory:
    def __init__(self, agent_name="agent"):
        self.agent_name = agent_name
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.messages = []
        self.tier_1_hot = []      # Full context (last 10 messages)
        self.tier_2_warm = []     # Summarized (last 20)
        self.tier_3_cold = []     # Metadata only (last 50)
        self.tier_4_archive = []  # Compressed history
        self.long_term = self._load_long_term()
        self.crystallized = self._load_crystallized()
        self.skill_usage = self._load_skill_usage()
        self.load_previous_session()
        self.last_summary = self._generate_session_summary()
        self._register_agent()
    
    def _register_agent(self):
        """Register this agent in the registry."""
        registry = self._load_registry()
        if self.agent_name not in registry or not isinstance(registry[self.agent_name], dict):
            registry[self.agent_name] = {
                "first_seen": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "session_count": 0,
                "skills_used": []
            }
        entry = registry[self.agent_name]
        for key in ["first_seen", "last_active", "session_count", "skills_used"]:
            if key not in entry:
                entry[key] = 0 if key == "session_count" else ([] if key == "skills_used" else datetime.now().isoformat())
        entry["last_active"] = datetime.now().isoformat()
        entry["session_count"] += 1
        self._save_registry(registry)
    
    def _load_registry(self):
        if REGISTRY_FILE.exists():
            try:
                data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return {item.get("agent_id", str(i)): item for i, item in enumerate(data)}
                if isinstance(data, dict):
                    return data
            except Exception as e:
                pass
        return {}
    
    def _save_registry(self, registry):
        with LOCK:
            REGISTRY_FILE.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    
    def _load_skill_usage(self):
        if SKILL_USAGE_FILE.exists():
            try:
                return json.loads(SKILL_USAGE_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                pass
        return {}
    
    def _save_skill_usage(self):
        with LOCK:
            SKILL_USAGE_FILE.write_text(json.dumps(self.skill_usage, indent=2), encoding="utf-8")
    
    def track_skill_usage(self, skill_name):
        """Track which skills are being used."""
        if skill_name not in self.skill_usage:
            self.skill_usage[skill_name] = {"count": 0, "last_used": None}
        self.skill_usage[skill_name]["count"] += 1
        self.skill_usage[skill_name]["last_used"] = datetime.now().isoformat()
        self._save_skill_usage()
    
    def get_unused_skills(self, threshold_days=7):
        """Find skills not used in last N days."""
        unused = []
        now = datetime.now()
        for skill, data in self.skill_usage.items():
            if data.get("last_used"):
                last = datetime.fromisoformat(data["last_used"])
                days = (now - last).days
                if days > threshold_days:
                    unused.append((skill, days))
        return sorted(unused, key=lambda x: x[1], reverse=True)
    
    def _generate_session_summary(self) -> str:
        """Generate compact session summary for next session (~50 tokens)."""
        if self.tier_1_hot:
            recent = [m.get("content", "")[:80] for m in self.tier_1_hot[-3:]]
            return f"Ongoing: {'; '.join(recent)}"
        return ""
    
    def get_session_context(self) -> dict:
        """
        Returns optimized context for next session.
        Uses tiered approach: crystallized → summary → recent.
        Total: ~100-200 tokens max.
        """
        return {
            "crystallized": self.crystallized[-5:] if self.crystallized else [],
            "summary": self.last_summary,
            "session_id": self.session_id,
            "projects_state": self._get_projects_state(),
            "agent": self.agent_name,
            "unused_skills": self.get_unused_skills()[:3]
        }
    
    def _get_projects_state(self) -> dict:
        """Get project states from crystallized learnings."""
        state = {}
        for item in self.crystallized:
            if "status" in item.get("value", "").lower():
                key = item.get("key", "")
                state[key] = item.get("value", "")[:100]
        return state
    
    def inject_context_prompt(self) -> str:
        """
        Generate context injection prompt for new session.
        Format: XML for efficient parsing.
        ~150 tokens max.
        """
        ctx = self.get_session_context()
        
        prompt = "<session_context>\n"
        
        if ctx["crystallized"]:
            prompt += "LEARNINGS:\n"
            for item in ctx["crystallized"]:
                prompt += f"- {item.get('key')}: {item.get('value', '')[:60]}\n"
        
        if ctx["projects_state"]:
            prompt += "\nPROJECTS:\n"
            for k, v in ctx["projects_state"].items():
                prompt += f"- {k}: {v}\n"
        
        if ctx["summary"]:
            prompt += f"\nONGOING: {ctx['summary']}\n"
        
        if ctx["unused_skills"]:
            prompt += f"\nUNUSED SKILLS: {ctx['unused_skills']}\n"
        
        prompt += f"\nSession ID: {ctx['session_id']}\n"
        prompt += f"Agent: {ctx['agent']}\n"
        prompt += "</session_context>"
        
        return prompt
    
    def _load_long_term(self):
        if MEMORY_FILE.exists():
            try:
                data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    base = _empty_memory()
                    for key in base:
                        if key in data:
                            base[key] = data[key]
                    return base
            except Exception as e:
                pass
        return _empty_memory()
    
    def _save_long_term(self):
        with LOCK:
            MEMORY_FILE.write_text(json.dumps(self.long_term, indent=2), encoding="utf-8")
    
    def _load_crystallized(self):
        """Try from both possible locations."""
        for f in [CRYSTALLIZED_FILE, CRYSTALLIZED_ALT]:
            if f.exists():
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    if isinstance(data, list) and len(data) > 0:
                        return data
                except Exception as e:
                    pass
        return []
    
    def _save_crystallized(self):
        with LOCK:
            CRYSTALLIZED_FILE.write_text(json.dumps(self.crystallized, indent=2), encoding="utf-8")
            CRYSTALLIZED_ALT.write_text(json.dumps(self.crystallized, indent=2), encoding="utf-8")
    
    def calculate_relevance(self, content):
        """Calculate relevance score (0-100) based on keywords."""
        content_lower = content.lower()
        score = 50
        
        # Boost for high-value keywords
        for kw in HIGH_KEYWORDS:
            if kw in content_lower:
                score += 15
        
        # Medium boost
        for kw in MEDIUM_KEYWORDS:
            if kw in content_lower:
                score += 8
        
        # Penalty for low-value
        for kw in LOW_KEYWORDS:
            if kw in content_lower:
                score -= 8
        
        # Boost for questions (user asking)
        if "?" in content:
            score += 10
        
        # Boost for code blocks
        if "```" in content:
            score += 12
        
        return max(0, min(100, score))
    
    def extract_keywords(self, content):
        """Extract meaningful keywords from content."""
        words = re.findall(r'\b\w{4,}\b', content.lower())
        stop_words = {"this", "that", "with", "from", "what", "when", "where", "which", "would", "could", "should"}
        keywords = [w for w in words if w not in stop_words]
        return Counter(keywords).most_common(5)
    
    def load_previous_session(self):
        """Restore context from most recent session."""
        sessions = sorted(SESSIONS_DIR.glob("session_*.json"), reverse=True)
        if sessions:
            try:
                data = json.loads(sessions[0].read_text(encoding="utf-8"))
                self.tier_2_warm = data.get("tier_2_warm", [])
                self.tier_3_cold = data.get("tier_3_cold", [])
                # Merge crystallized if newer
                prev_crystal = data.get("crystallized", [])
                for item in prev_crystal:
                    if item not in self.crystallized:
                        self.crystallized.append(item)
                print(f"[Memory] Restored from {sessions[0].name}")
            except Exception as e:
                print(f"[Memory] Could not restore: {e}")
    
    def add(self, category, key, value):
        """Add to long-term memory."""
        category = category.lower()
        if category in self.long_term:
            self.long_term[category][key] = value
        self._save_long_term()
    
    def get(self, category, key=None):
        """Retrieve from long-term memory."""
        category = category.lower()
        if category in self.long_term:
            if key:
                return self.long_term[category].get(key)
            return self.long_term[category]
        return None
    
    def add_message(self, role, content):
        """Add a message with automatic tier classification."""
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "relevance": self.calculate_relevance(content),
            "keywords": self.extract_keywords(content)
        }
        self.messages.append(msg)
        
        relevance = msg["relevance"]
        
        if relevance >= 80:
            self.tier_1_hot.append(msg)
            if len(self.tier_1_hot) > 10:
                demoted = self.tier_1_hot.pop(0)
                self.tier_2_warm.append(self._compress_message(demoted, 0.4))
        elif relevance >= 50:
            self.tier_2_warm.append(msg)
            if len(self.tier_2_warm) > 20:
                demoted = self.tier_2_warm.pop(0)
                self.tier_3_cold.append(self._compress_message(demoted, 0.7))
        else:
            self.tier_3_cold.append(msg)
            if len(self.tier_3_cold) > 50:
                self.tier_3_cold.pop(0)
        
        self._save_session()
        return msg
    
    def _compress_message(self, msg, ratio=0.4):
        """Compress message based on ratio."""
        content = msg.get("content", "")
        if len(content) > 200:
            if ratio >= 0.7:
                # Heavy compression: just keywords
                keywords = self.extract_keywords(content)
                compressed = " ".join(f"{w}({c})" for w, c in keywords)
            elif ratio >= 0.4:
                # Medium: first sentence + key points
                sentences = content.split(". ")
                compressed = sentences[0][:100] if sentences else content[:100]
            else:
                compressed = content[:int(len(content) * ratio)]
            return {
                "role": msg["role"],
                "content": compressed,
                "timestamp": msg["timestamp"],
                "compressed": True,
                "original_length": len(content)
            }
        return msg
    
    def get_context(self, max_messages=10):
        """Get optimized context for current session."""
        context = []
        for msg in reversed(self.tier_1_hot[-5:]):
            context.append(msg)
        for msg in reversed(self.tier_2_warm[-5:]):
            context.append(msg)
        return list(reversed(context))[-max_messages:]
    
    def crystallize(self, key, value):
        """Add to permanent crystallized knowledge."""
        for item in self.crystallized:
            if item.get("key") == key:
                item["value"] = value
                item["updated"] = datetime.now().isoformat()
                self._save_crystallized()
                return
        self.crystallized.append({
            "key": key,
            "value": value,
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat()
        })
        self._save_crystallized()
    
    def get_crystallized(self, key=None):
        """Retrieve crystallized knowledge."""
        if key:
            for item in self.crystallized:
                if item.get("key") == key:
                    return item.get("value")
            return None
        return self.crystallized
    
    def rag_query(self, query, max_results=3):
        """
        Simple RAG: Search knowledge base for relevant context.
        Returns relevant snippets to inject into prompt.
        """
        if not KNOWLEDGE_BASE.exists():
            return []
        
        results = []
        query_lower = query.lower()
        query_keywords = set(re.findall(r'\b\w{4,}\b', query_lower))
        
        for md_file in KNOWLEDGE_BASE.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                content_lower = content.lower()
                
                # Score based on keyword matches
                score = 0
                for kw in query_keywords:
                    score += content_lower.count(kw)
                
                if score > 0:
                    # Extract relevant snippet (first match + context)
                    idx = content_lower.find(next(iter(query_keywords), ""))
                    if idx >= 0:
                        start = max(0, idx - 100)
                        end = min(len(content), idx + 300)
                        snippet = content[start:end]
                        results.append({
                            "file": md_file.name,
                            "score": score,
                            "snippet": snippet[:200]
                        })
            except Exception as e:
                pass
        
        return sorted(results, key=lambda x: x["score"], reverse=True)[:max_results]
    
    def _save_session(self):
        """Save current session state."""
        session_file = SESSIONS_DIR / f"session_{self.session_id}.json"
        data = {
            "session_id": self.session_id,
            "agent": self.agent_name,
            "created": self.session_id,
            "tier_1_hot": self.tier_1_hot[-5:],
            "tier_2_warm": self.tier_2_warm[-10:],
            "tier_3_cold": self.tier_3_cold[-20:],
            "crystallized": self.crystallized[-5:]
        }
        with LOCK:
            session_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    def save(self):
        """Manual save trigger."""
        self._save_long_term()
        self._save_session()
    
    def get_stats(self):
        """Return memory statistics."""
        return {
            "session_id": self.session_id,
            "agent": self.agent_name,
            "messages": len(self.messages),
            "tier_1": len(self.tier_1_hot),
            "tier_2": len(self.tier_2_warm),
            "tier_3": len(self.tier_3_cold),
            "crystallized": len(self.crystallized),
            "long_term_categories": list(self.long_term.keys()),
            "skill_usage_count": len(self.skill_usage)
        }


def load_memory(agent_name="agent"):
    """Factory function to load/create memory."""
    return UnifiedMemory(agent_name)


if __name__ == "__main__":
    mem = load_memory("opencode")
    print("UnifiedMemory v2.0 loaded")
    print(f"Stats: {mem.get_stats()}")
    print(f"\nContext prompt:\n{mem.inject_context_prompt()}")
    
    # Test RAG
    results = mem.rag_query("Python security best practices")
    print(f"\nRAG results for 'Python security': {len(results)} found")
    for r in results:
        print(f"  - {r['file']}: {r['snippet'][:50]}...")
