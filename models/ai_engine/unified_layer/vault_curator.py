"""
Automated Vault Curation - Auto-create and update notes from conversations
Works with Unified Layer to grow the vault organically as agents learn.
"""

import json
import os
import re
import os
from pathlib import Path
from datetime import datetime
from collections import Counter

VAULT_PATH = Path(os.environ.get("LAIS_VAULT_PATH", r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain"))
MEMORY_DIR = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge\memory")
CURATOR_LOG = MEMORY_DIR / "curator_log.json"
FOLDER_ROUTING = {
    "10_Resources": ["python", "programming", "code", "software", "development", "algorithm", "api", "database", "web", "linux", "windows", "automation"],
    "30_Research": ["research", "study", "analysis", "trend", "report", "investigation", "findings", "benchmark", "comparison", "survey"],
    "20_Skills": ["skill", "capability", "ability", "tool", "plugin", "extension", "feature"],
    "40_System": ["protocol", "system", "configuration", "setup", "agent", "integration", "architecture", "memory", "session"],
    "50_Memory": ["memory", "recall", "learn", "experience", "session", "crystallized", "knowledge"],
    "00_Inbox": []  # Default for uncategorized
}

AGENT_FOLDER_OWNERSHIP = {
    "lais": ["50_Memory", "00_Inbox", "40_System"],
    "jarvis": ["50_Memory", "10_Resources", "30_Research"],
    "opencode": ["20_Skills", "30_Projects", "10_Resources"],
    "system": ["40_System", "00_Map_of_Content"],
    "unknown": ["00_Inbox", "50_Memory"],
}

AGENT_WRITE_DENY = {
    "lais": ["20_Skills", "30_Projects"],
    "jarvis": ["20_Skills", "30_Projects"],
    "opencode": ["40_System"],
    "system": [],
    "unknown": ["10_Resources", "20_Skills", "30_Projects", "40_System"],
}

class OwnershipGuardError(Exception):
    pass

def check_folder_permission(agent, folder):
    if agent in AGENT_WRITE_DENY and folder in AGENT_WRITE_DENY[agent]:
        return False, f"Agent '{agent}' is not permitted to write to '{folder}'"
    if agent in AGENT_FOLDER_OWNERSHIP and folder not in AGENT_FOLDER_OWNERSHIP[agent]:
        pass
    return True, "OK"

PREFIX_CONVENTIONS = {
    "Log": ["log", "session", "activity", "event", "conversation"],
    "Project": ["project", "build", "feature", "initiative", "implementation"],
    "Person": ["person", "contact", "user", "profile"],
    "Meeting": ["meeting", "sync", "standup", "review"],
    "Spec": ["spec", "specification", "requirements", "design"],
    "Guide": ["guide", "tutorial", "howto", "instructions", "walkthrough"],
    "Daily": ["daily", "journal", "today", "diary"],
}

def determine_prefix(title, content):
    """Determine appropriate prefix for note based on content analysis."""
    combined = f"{title} {content}".lower()
    
    for prefix, keywords in PREFIX_CONVENTIONS.items():
        for kw in keywords:
            if kw in combined:
                return prefix
    
    return None

def apply_prefix_to_filename(filename, prefix):
    """Apply prefix naming convention to filename if not already present."""
    if prefix and not filename.lower().startswith(prefix.lower()):
        return f"{prefix} - {filename}"
    return filename

STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "shall",
    "can", "need", "dare", "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
    "from", "as", "into", "through", "during", "before", "after", "above", "below", "between",
    "out", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "just", "because",
    "but", "and", "or", "if", "while", "this", "that", "these", "those", "it", "its", "i", "me",
    "my", "we", "our", "you", "your", "he", "him", "his", "she", "her", "they", "them", "their",
    "what", "which", "who", "whom", "about"
}


def extract_topics(text, max_topics=5):
    """Extract key topics from text using frequency analysis."""
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    return [word for word, _ in Counter(filtered).most_common(max_topics)]


def determine_folder(title, content):
    """Determine best folder for a note based on title/content."""
    combined = f"{title} {content}".lower()
    scores = Counter()
    
    for folder, keywords in FOLDER_ROUTING.items():
        for kw in keywords:
            if kw in combined:
                scores[folder] += 1
    
    if scores:
        return scores.most_common(1)[0][0]
    return "00_Inbox"


def find_existing_note(topic):
    """Find if a note about this topic already exists."""
    topic_lower = topic.lower().replace(" ", "_")
    
    for md_file in VAULT_PATH.rglob("*.md"):
        if md_file.name == "Welcome.md" or md_file.name.startswith("_"):
            continue
        
        filename_lower = md_file.stem.lower().replace(" ", "_")
        if topic_lower in filename_lower or filename_lower in topic_lower:
            return md_file
        
        content = md_file.read_text(encoding="utf-8", errors="ignore").lower()
        if topic_lower in content[:500]:
            return md_file
    
    return None


def generate_yaml_frontmatter(title, topics, folder):
    """Generate YAML frontmatter for a note."""
    tags = [f"auto/{folder.lower().replace('_', '-')}", f"topic/{topics[0]}"] if topics else []
    if len(topics) > 1:
        tags.append(f"topic/{topics[1]}")
    if len(topics) > 2:
        tags.append(f"topic/{topics[2]}")
    now = datetime.now().isoformat()
    
    return f"""---
title: "{title}"
created: {now}
updated: {now}
folder: {folder}
tags: [{', '.join(tags)}]
source: ai_curation
---
"""


def create_wikilinks(content, existing_titles):
    """Convert topic references to wikilinks."""
    linked = content
    for title in existing_titles:
        if title.lower() in content.lower() and f"[[{title}]]" not in content:
            pattern = re.compile(re.escape(title), re.IGNORECASE)
            linked = pattern.sub(f"[[{title}]]", linked, count=1)
    return linked


def get_existing_titles():
    """Get titles of all existing notes for wikilinking."""
    titles = []
    for md_file in VAULT_PATH.rglob("*.md"):
        if md_file.name == "Welcome.md" or md_file.name.startswith("_"):
            continue
        title = md_file.stem.replace("_", " ").title()
        titles.append(title)
    return titles


class VaultCurator:
    """Automatically curates the vault based on conversations."""
    
    def __init__(self):
        self.log = self._load_log()
    
    def _load_log(self):
        """Load curator action log."""
        if CURATOR_LOG.exists():
            try:
                return json.loads(CURATOR_LOG.read_text(encoding="utf-8"))
            except Exception as e:
                return []
        return []
    
    def _save_log(self):
        """Save curator log."""
        CURATOR_LOG.write_text(json.dumps(self.log[-100:], indent=2), encoding="utf-8")
    
    def process_conversation(self, user_message, ai_response, agent="unknown"):
        """Main curation pipeline - analyzes conversation and updates vault."""
        actions = []
        
        combined = f"{user_message}\n{ai_response}"
        topics = extract_topics(combined, max_topics=5)
        
        for topic in topics:
            existing = find_existing_note(topic)
            
            if existing:
                result = self._update_note(existing, combined, topic)
                if result:
                    actions.append(result)
            else:
                result = self._create_note(topic, combined, agent)
                if result:
                    actions.append(result)
        
        if actions:
            self.log.append({
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "actions": actions,
                "summary": f"Processed {len(actions)} updates"
            })
            self._save_log()
        
        return actions
    
    def _create_note(self, topic, content, agent):
        title = topic.replace("_", " ").title()
        folder = determine_folder(title, content)
        
        permitted, reason = check_folder_permission(agent, folder)
        if not permitted:
            folder = "00_Inbox"
        
        if not (VAULT_PATH / folder).exists():
            folder = "00_Inbox"
        
        existing_titles = get_existing_titles()
        clean_content = self._extract_clean_content(content, topic)
        topics = extract_topics(content, 3)
        
        prefix = determine_prefix(title, clean_content)
        if prefix:
            title = f"{prefix} - {title}"
        
        yaml = generate_yaml_frontmatter(title, topics, folder)
        
        note_content = f"{yaml}\n# {title}\n\n{clean_content}\n\n## Related\n"
        note_content = create_wikilinks(note_content, existing_titles)
        
        filename = topic.replace(" ", "_")[:60]
        if prefix:
            filename = apply_prefix_to_filename(filename, prefix)
        note_path = VAULT_PATH / folder / f"{filename}.md"
        
        if note_path.exists():
            return None
        
        try:
            note_path.write_text(note_content, encoding="utf-8")
            return {
                "action": "created",
                "file": str(note_path.relative_to(VAULT_PATH)),
                "topic": topic,
                "agent": agent
            }
        except Exception as e:
            return None
    
    def _update_note(self, filepath, new_content, topic):
        """Update an existing note with new information."""
        try:
            current = filepath.read_text(encoding="utf-8")
            clean = self._extract_clean_content(new_content, topic)
            
            if "## Latest Updates" not in current:
                current += "\n## Latest Updates\n"
            
            now = datetime.now().strftime("%Y-%m-%d")
            update_section = f"\n### {now}\n{clean[:300]}\n"
            current += update_section
            
            now_iso = datetime.now().isoformat()
            if "updated:" in current:
                lines = current.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("updated:"):
                        lines[i] = f"updated: {now_iso}"
                        break
                current = "\n".join(lines)
            
            filepath.write_text(current, encoding="utf-8")
            
            return {
                "action": "updated",
                "file": str(filepath.relative_to(VAULT_PATH)),
                "topic": topic
            }
        except Exception as e:
            return None
    
    def _extract_clean_content(self, content, topic):
        """Extract relevant content about the topic, removing noise."""
        lines = content.split("\n")
        relevant = []
        
        in_topic = False
        for line in lines:
            if topic.lower().replace("_", " ") in line.lower():
                in_topic = True
            if in_topic and line.strip():
                relevant.append(line)
            if len(relevant) > 20:
                break
        
        if not relevant:
            return content[:500]
        
        return "\n".join(relevant)[:500]
    
    def get_curator_stats(self):
        """Get statistics about curation activity."""
        created = sum(1 for entry in self.log for action in entry.get("actions", []) if action.get("action") == "created")
        updated = sum(1 for entry in self.log for action in entry.get("actions", []) if action.get("action") == "updated")
        
        return {
            "total_actions": len(self.log),
            "notes_created": created,
            "notes_updated": updated,
            "last_activity": self.log[-1]["timestamp"] if self.log else None
        }
    
    def suggest_vault_improvements(self):
        """Suggest improvements based on current vault state."""
        suggestions = []
        
        notes_without_tags = 0
        notes_without_wikilinks = 0
        inbox_count = 0
        
        for md_file in VAULT_PATH.rglob("*.md"):
            if md_file.name.startswith("_") or md_file.name == "Welcome.md":
                continue
            
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            
            if "tags:" not in content[:200]:
                notes_without_tags += 1
            
            if "[[" not in content:
                notes_without_wikilinks += 1
            
            if md_file.parent.name == "00_Inbox":
                inbox_count += 1
        
        if inbox_count > 10:
            suggestions.append(f"Move {inbox_count} notes from Inbox to proper folders")
        if notes_without_tags > 10:
            suggestions.append(f"Add tags to {notes_without_tags} notes")
        if notes_without_wikilinks > 20:
            suggestions.append(f"Add wikilinks to {notes_without_wikilinks} isolated notes")
        
        return suggestions
    
    def compute_daily_priority(self, user_message, ai_response) -> dict:
        priority_signals = {
            "urgent": ["urgent", "asap", "immediately", "critical", "emergency", "broken", "crash"],
            "important": ["important", "priority", "deadline", "must", "need to", "should"],
            "work": ["code", "build", "implement", "deploy", "fix", "debug", "test"],
            "growth": ["learn", "study", "research", "understand", "explain", "how does"],
            "legacy": ["system", "architecture", "framework", "infrastructure", "automation", "protocol"],
        }
        
        combined = f"{user_message} {ai_response}".lower()
        scores = {}
        
        for category, keywords in priority_signals.items():
            score = sum(3 for kw in keywords if kw in combined)
            scores[category] = score
        
        psp_order = ["urgent", "important", "work", "growth", "legacy"]
        ranked = sorted(scores.items(), key=lambda x: psp_order.index(x[0]) if x[0] in psp_order else 99)
        
        dominant = ranked[0][0] if ranked else "work"
        confidence = max(s[1] for s in scores.values()) if scores else 0
        
        return {
            "category": dominant,
            "scores": scores,
            "confidence": confidence,
            "psp_level": 7 if dominant == "urgent" else 6 if dominant == "important" else 3 if dominant == "work" else 2 if dominant == "growth" else 1
        }


def load_curator():
    """Factory function to load curator."""
    return VaultCurator()


if __name__ == "__main__":
    curator = load_curator()
    
    print("=== Vault Curator ===")
    stats = curator.get_curator_stats()
    print(f"Total actions: {stats['total_actions']}")
    print(f"Notes created: {stats['notes_created']}")
    print(f"Notes updated: {stats['notes_updated']}")
    
    print("\n=== Suggestions ===")
    for s in curator.suggest_vault_improvements():
        print(f"  - {s}")
    
    print("\n=== Test: Process Conversation ===")
    test_user = "How does Python handle memory management with garbage collection?"
    test_ai = "Python uses automatic garbage collection with reference counting and a cyclic garbage collector. Objects are freed when reference count reaches zero. The gc module handles circular references. You can tune gc thresholds with gc.set_threshold()."
    
    actions = curator.process_conversation(test_user, test_ai, "test")
    for a in actions:
        print(f"  {a['action']}: {a.get('file', a.get('topic'))}")
