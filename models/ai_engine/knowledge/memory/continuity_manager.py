import json
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SESSIONS_DIR = BASE_DIR / "knowledge" / "sessions"
MEMORY_DIR = BASE_DIR / "knowledge" / "memory"

SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

HIGH_KEYWORDS = {"current", "active", "now", "working", "focus", "session", "continuity", "protocol", "automated", "code", "fix", "bug", "error", "implement", "create", "lais", "ai"}
MEDIUM_KEYWORDS = {"method", "approach", "technique", "specification", "insight", "system", "function", "class", "file", "project"}
LOW_KEYWORDS = {"background", "history", "archive", "example", "test", "demo", "old", "previous", "yesterday"}


class ContinuityManager:
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.messages = []
        self.tier_1_hot = []
        self.tier_2_warm = []
        self.tier_3_cold = []
        self.crystallized = self._load_crystallized()
        self.load_previous_session()
    
    def _load_crystallized(self):
        path = MEMORY_DIR / "crystallized_knowledge.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                return []
        return []
    
    def _save_crystallized(self):
        path = MEMORY_DIR / "crystallized_knowledge.json"
        path.write_text(json.dumps(self.crystallized, indent=2), encoding="utf-8")
    
    def load_previous_session(self):
        sessions = sorted(SESSIONS_DIR.glob("session_*.json"), reverse=True)
        if sessions:
            try:
                data = json.loads(sessions[0].read_text(encoding="utf-8"))
                self.session_id = data.get("session_id", self.session_id)
                self.tier_2_warm = data.get("tier_2_warm", [])
                self.tier_3_cold = data.get("tier_3_cold", [])
                print(f"[Continuity] Restored from {sessions[0].name}")
            except Exception as e:
                print(f"[Continuity] Could not restore: {e}")
    
    def calculate_relevance(self, content):
        content_lower = content.lower()
        score = 50
        for kw in HIGH_KEYWORDS:
            if kw in content_lower:
                score += 15
        for kw in MEDIUM_KEYWORDS:
            if kw in content_lower:
                score += 8
        for kw in LOW_KEYWORDS:
            if kw in content_lower:
                score -= 8
        return max(0, min(100, score))
    
    def add_message(self, role, content):
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "relevance": self.calculate_relevance(content)
        }
        self.messages.append(msg)
        
        if msg["relevance"] >= 80:
            self.tier_1_hot.append(msg)
            if len(self.tier_1_hot) > 10:
                demoted = self.tier_1_hot.pop(0)
                self.tier_2_warm.append(self._compress_message(demoted, 0.4))
        elif msg["relevance"] >= 60:
            self.tier_2_warm.append(self._compress_message(msg, 0.4))
            if len(self.tier_2_warm) > 50:
                archived = self.tier_2_warm.pop(0)
                self.tier_3_cold.append(self._compress_message(archived, 0.7))
        elif msg["relevance"] >= 40:
            self.tier_3_cold.append(self._compress_message(msg, 0.7))
        else:
            self.tier_3_cold.append(self._compress_message(msg, 0.85))
        
        if len(self.messages) >= 50:
            self.archive_session()
        
        return msg
    
    def _compress_message(self, msg, level):
        content = msg.get("content", "")
        if level >= 0.85:
            words = content.split()
            keywords = [w for w in words if len(w) > 3][:5]
            compressed = " ".join(keywords)
        elif level >= 0.7:
            sentences = content.split(". ")
            compressed = sentences[0][:100] if sentences else content[:100]
        else:
            compressed = content[:200]
        
        return {
            "role": msg.get("role"),
            "compressed": compressed,
            "timestamp": msg.get("timestamp"),
            "relevance": msg.get("relevance")
        }
    
    def archive_session(self):
        session_data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "message_count": len(self.messages),
            "tier_1_hot": self.tier_1_hot[-5:],
            "tier_2_warm": self.tier_2_warm[-20:],
            "tier_3_cold": self.tier_3_cold[-50:],
            "crystallized": self.crystallized[-10:]
        }
        
        session_file = SESSIONS_DIR / f"session_{self.session_id}.json"
        session_file.write_text(json.dumps(session_data, indent=2), encoding="utf-8")
        print(f"[Continuity] Session archived: {session_file.name}")
        
        self.tier_2_warm = self.tier_2_warm[-20:]
        self.tier_3_cold = self.tier_3_cold[-50:]
    
    def get_context_summary(self):
        hot_context = [m["content"][:150] for m in self.tier_1_hot[-3:]]
        warm_summary = [m.get("compressed", "")[:80] for m in self.tier_2_warm[-5:]]
        
        return {
            "session_id": self.session_id,
            "messages": len(self.messages),
            "current_focus": hot_context[-1] if hot_context else "",
            "recent_context": " | ".join(warm_summary[-3:]),
            "crystallized": self.crystallized[-5:]
        }
    
    def export_for_continuity(self):
        return json.dumps({
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "tier_1_hot": self.tier_1_hot[-5:],
            "tier_2_warm": self.tier_2_warm[-10:],
            "tier_3_cold": self.tier_3_cold[-20:],
            "crystallized": self.crystallized[-5:],
            "continuity_note": "Paste this JSON at session start for context continuity"
        }, indent=2)


continuity = ContinuityManager()


def add_to_context(role, content):
    return continuity.add_message(role, content)


def get_context():
    return continuity.get_context_summary()


def export_session():
    return continuity.export_for_continuity()


if __name__ == "__main__":
    continuity.add_message("user", "I want to build an AI assistant called Omnis")
    continuity.add_message("assistant", "I'll help you create LAIS with memory continuity")
    continuity.add_message("user", "It should remember previous sessions")
    print(json.dumps(continuity.get_context_summary(), indent=2))
    print("\n--- Export for continuity ---")
    print(continuity.export_for_continuity())