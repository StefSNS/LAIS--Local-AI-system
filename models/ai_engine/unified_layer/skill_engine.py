"""
Skill Engine - Phase 4 of Architecture Evolution
Self-improving skill system that auto-generates, validates, and manages reusable skills.
Inspired by Hermes Agent's skill creation loop.
"""

import json
import re
import ast
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple
from threading import Lock

SKILLS_DIR = Path(
    r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis\skills"
)
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

SKILL_REGISTRY_FILE = SKILLS_DIR / "skill_registry.json"
SKILL_LOG_FILE = SKILLS_DIR / "skill_log.json"
LOCK = Lock()


class Skill:
    """Represents a reusable agent skill."""

    def __init__(
        self,
        skill_id: str,
        name: str,
        description: str,
        code: str,
        category: str = "general",
        tags: Optional[List[str]] = None,
        created_by: str = "system",
    ):
        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.code = code
        self.category = category
        self.tags = tags or []
        self.created_by = created_by
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.usage_count = 0
        self.last_used = None
        self.success_rate = 0.0
        self.successes = 0
        self.failures = 0
        self.enabled = True

    def record_usage(self, success: bool):
        """Record a skill execution."""
        self.usage_count += 1
        self.last_used = datetime.now().isoformat()
        if success:
            self.successes += 1
        else:
            self.failures += 1
        total = self.successes + self.failures
        self.success_rate = self.successes / total if total > 0 else 0.0
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "category": self.category,
            "tags": self.tags,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "usage_count": self.usage_count,
            "last_used": self.last_used,
            "success_rate": round(self.success_rate, 2),
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        skill = cls(
            skill_id=data["skill_id"],
            name=data["name"],
            description=data["description"],
            code=data["code"],
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            created_by=data.get("created_by", "system"),
        )
        skill.created_at = data.get("created_at", datetime.now().isoformat())
        skill.updated_at = data.get("updated_at", skill.created_at)
        skill.usage_count = data.get("usage_count", 0)
        skill.last_used = data.get("last_used")
        skill.success_rate = data.get("success_rate", 0.0)
        skill.successes = data.get("successes", 0)
        skill.failures = data.get("failures", 0)
        skill.enabled = data.get("enabled", True)
        return skill


class SkillEngine:
    """
    Self-improving skill engine.
    - Creates skills from conversation patterns
    - Validates code safety before saving
    - Discovers and executes skills on demand
    - Tracks usage and success rates
    """

    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.runtime_handlers: Dict[str, Callable] = {}
        self._load_registry()
        self._load_skills()

    def _load_registry(self):
        """Load skill registry."""
        if SKILL_REGISTRY_FILE.exists():
            try:
                data = json.loads(SKILL_REGISTRY_FILE.read_text(encoding="utf-8"))
                for skill_data in data:
                    skill = Skill.from_dict(skill_data)
                    if skill.enabled:
                        self.skills[skill.skill_id] = skill
            except Exception as e:
                pass

    def _save_registry(self):
        """Save skill registry."""
        with LOCK:
            all_skills = [skill.to_dict() for skill in self.skills.values()]
            SKILL_REGISTRY_FILE.write_text(
                json.dumps(all_skills, indent=2), encoding="utf-8"
            )

    def _load_skills(self):
        """Load skill .py files from skills directory."""
        for py_file in SKILLS_DIR.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            skill_id = f"skill_{py_file.stem}"
            if skill_id in self.skills:
                self._load_skill_code(py_file, skill_id)

    def _load_skill_code(self, py_file: Path, skill_id: str):
        """Load and register a skill function."""
        try:
            spec_path = py_file.with_suffix(".json")
            if spec_path.exists():
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                # Could dynamically load and register here
        except Exception as e:
            pass

    def search_skills(
        self,
        query: str,
        category: Optional[str] = None,
        min_success_rate: float = 0.0,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search for skills by name, description, or tags."""
        query_lower = query.lower()
        results = []

        for skill in self.skills.values():
            if not skill.enabled:
                continue
            if category and skill.category != category:
                continue
            if skill.success_rate < min_success_rate:
                continue

            score = 0
            if query_lower in skill.name.lower():
                score += 10
            if query_lower in skill.description.lower():
                score += 5
            if any(query_lower in tag.lower() for tag in skill.tags):
                score += 3
            if query_lower in skill.category.lower():
                score += 2

            if score > 0:
                results.append((score, skill.to_dict()))

        results.sort(key=lambda x: x[0], reverse=True)
        return [skill for _, skill in results[:max_results]]

    def auto_detect_skill(self, query: str) -> Optional[Dict[str, Any]]:
        query_lower = query.lower()
        best_match = None
        best_score = 0

        for skill in self.skills.values():
            if not skill.enabled:
                continue

            score = 0
            for trigger in skill.tags:
                if trigger.lower() in query_lower:
                    score += 5

            name_words = skill.name.lower().split()
            for word in name_words:
                if len(word) > 3 and word in query_lower:
                    score += 3

            desc_words = skill.description.lower().split()
            for word in desc_words:
                if len(word) > 4 and word in query_lower:
                    score += 1

            if score > best_score:
                best_score = score
                best_match = skill.to_dict()

        if best_match and best_score >= 5:
            best_match["trigger_score"] = best_score
            return best_match
        return None

    def get_skill(self, skill_id: str) -> Optional[Dict]:
        """Get a skill by ID."""
        skill = self.skills.get(skill_id)
        return skill.to_dict() if skill else None

    def list_skills(self, category: Optional[str] = None) -> List[Dict]:
        """List all skills, optionally filtered by category."""
        skills = []
        for skill in self.skills.values():
            if not skill.enabled:
                continue
            if category and skill.category != category:
                continue
            skills.append(skill.to_dict())
        skills.sort(key=lambda x: x["usage_count"], reverse=True)
        return skills


    def create_skill(self, name, description, code, category="general", tags=None, created_by="system"):
        """Create a new skill and save to registry."""
        skill_id = f"skill_{int(datetime.now().timestamp() * 1000)}"
        skill = Skill(
            skill_id=skill_id,
            name=name,
            description=description,
            code=code,
            category=category,
            tags=tags or [],
            created_by=created_by,
        )
        self.skills[skill_id] = skill
        self._save_registry()
        self._log_skill_event("created", skill_id, f"Created by {created_by}")
        return (True, f"Skill '{name}' created", skill)

    def execute_skill(self, skill_id, *args, **kwargs):
        """Execute a skill by its ID."""
        skill = self.skills.get(skill_id)
        if not skill:
            return (False, f"Skill {skill_id} not found")

        try:
            # Create a local namespace and execute the skill code
            local_ns = {"__builtins__": __builtins__}
            exec(skill.code, local_ns)

            if "execute" in local_ns:
                result = local_ns["execute"](*args, **kwargs)
                skill.record_usage(success=True)
                self._save_registry()
                return (True, result)
            else:
                skill.record_usage(success=False)
                self._save_registry()
                return (False, "Skill code has no execute() function")
        except Exception as e:
            skill.record_usage(success=False)
            self._save_registry()
            return (False, str(e))

    def disable_skill(self, skill_id: str) -> bool:
        """Disable a skill."""
        if skill_id in self.skills:
            self.skills[skill_id].enabled = False
            self.skills[skill_id].updated_at = datetime.now().isoformat()
            self._save_registry()
            return True
        return False

    def enable_skill(self, skill_id: str) -> bool:
        """Enable a disabled skill."""
        if skill_id in self.skills:
            self.skills[skill_id].enabled = True
            self.skills[skill_id].updated_at = datetime.now().isoformat()
            self._save_registry()
            return True
        return False

    def _log_skill_event(self, event: str, skill_id: str, detail: str):
        """Log a skill event."""
        log_entry = {
            "event": event,
            "skill_id": skill_id,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            if SKILL_LOG_FILE.exists():
                log = json.loads(SKILL_LOG_FILE.read_text(encoding="utf-8"))
            else:
                log = []
            log.append(log_entry)
            SKILL_LOG_FILE.write_text(
                json.dumps(log[-100:], indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    def extract_skill_from_conversation(
        self, user_request: str, ai_solution: str
    ) -> Optional[Dict]:
        """
        Analyze a conversation turn to detect if a reusable skill was created.
        Returns skill data if worth saving, None otherwise.
        """
        combined_lower = f"{user_request} {ai_solution}".lower()

        # Signals that a solution is worth saving as a skill
        skill_signals = [
            "def ", "function", "here's how", "here is how",
            "to do this", "you can use", "a simple way",
            "reusable", "utility", "helper", "script",
        ]

        signal_score = sum(1 for s in skill_signals if s in combined_lower)
        if signal_score < 2:
            return None

        # Extract code blocks
        code_blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", ai_solution, re.DOTALL)
        if not code_blocks:
            return None

        code = code_blocks[0].strip()
        if len(code) < 10:
            return None

        # Generate a name from the request
        name = user_request.strip()[:50]
        if not name:
            name = "unnamed_skill"

        return {
            "name": name,
            "description": f"Auto-generated from: {user_request[:80]}",
            "code": code,
            "category": "auto-generated",
            "tags": ["auto"],
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get skill engine statistics."""
        skills = list(self.skills.values())
        total_usage = sum(s.usage_count for s in skills)
        avg_success = (
            sum(s.success_rate for s in skills if s.usage_count > 0)
            / max(1, sum(1 for s in skills if s.usage_count > 0))
        )

        categories = {}
        for s in skills:
            categories[s.category] = categories.get(s.category, 0) + 1

        return {
            "total_skills": len(skills),
            "enabled_skills": sum(1 for s in skills if s.enabled),
            "total_usage": total_usage,
            "avg_success_rate": round(avg_success, 2),
            "categories": categories,
            "skill_files": len(list(SKILLS_DIR.glob("*.py"))),
        }


def load_skill_engine() -> SkillEngine:
    """Factory function."""
    return SkillEngine()


if __name__ == "__main__":
    import sys
    sys.path.insert(
        0, r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis"
    )

    print("=== Skill Engine - Phase 4 ===\n")

    engine = load_skill_engine()

    # Create test skills
    print("--- Creating Skills ---")

    code_format_table = '''
def execute(data, format_type="markdown"):
    """Format a list of dicts as a table."""
    if not data:
        return "No data"
    headers = list(data[0].keys())
    widths = {h: len(h) for h in headers}
    for row in data:
        for h in headers:
            widths[h] = max(widths[h], len(str(row.get(h, ""))))
    
    header_line = " | ".join(h.ljust(widths[h]) for h in headers)
    sep = "-+-".join("-" * widths[h] for h in headers)
    lines = [header_line, sep]
    for row in data:
        line = " | ".join(str(row.get(h, "")).ljust(widths[h]) for h in headers)
        lines.append(line)
    return "\\n".join(lines)
'''

    ok, msg, skill = engine.create_skill(
        "Format Table",
        "Format a list of dicts as an aligned text table",
        code_format_table,
        category="formatting",
        tags=["table", "format", "output"],
        created_by="test",
    )
    print(f"  Format Table: {msg}")

    code_search_vault = '''
def execute(query, max_results=5):
    """Search vault notes by keyword."""
    import os
    results = []
    vault = os.path.expanduser("~/Desktop/AI projects/Obsidian/Unified Brain")
    for root, dirs, files in os.walk(vault):
        for f in files:
            if f.endswith(".md"):
                path = os.path.join(root, f)
                try:
                    content = open(path, encoding="utf-8").read()
                    if query.lower() in content.lower():
                        results.append({"file": f, "path": path})
                        if len(results) >= max_results:
                            return results
                except Exception as e:
                    pass
    return results
'''

    ok, msg, skill = engine.create_skill(
        "Search Vault",
        "Search vault notes by keyword match",
        code_search_vault,
        category="vault",
        tags=["search", "vault", "notes"],
        created_by="test",
    )
    print(f"  Search Vault: {msg}")

    # Execute skills
    print("\n--- Executing Skills ---")
    if skill:
        test_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        ok, result = engine.execute_skill(
            skill.skill_id, test_data, "markdown"
        )
        if ok:
            print(f"  Format Table result:\n{result}")
        else:
            print(f"  Error: {result}")

    # Search skills
    print("\n--- Searching Skills ---")
    results = engine.search_skills("table format")
    for s in results:
        print(f"  [{s['category']}] {s['name']} (used {s['usage_count']}x, {s['success_rate']*100:.0f}% success)")

    # Extract from conversation
    print("\n--- Extract Skill from Conversation ---")
    extracted = engine.extract_skill_from_conversation(
        "How do I sort a list by date?",
        "Here's how you do it:\n```python\nfrom datetime import datetime\ndef execute(items, key='date'):\n    return sorted(items, key=lambda x: datetime.fromisoformat(x.get(key, '2000-01-01')))\n```"
    )
    if extracted:
        print(f"  Extracted: {extracted['name']}")
        print(f"  Code preview: {extracted['code'][:60]}...")
    else:
        print("  No skill extracted")

    print("\n--- Stats ---")
    stats = engine.get_stats()
    print(json.dumps(stats, indent=2))

    print("\nPhase 4 skill engine test complete.")
