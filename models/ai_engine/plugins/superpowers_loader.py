"""
Superpowers Skill Loader - Loads Obra/Superpowers skills for LAIS.
Adapts OpenCode SKILL.md files for Python-based LAIS plugins.

Skills loaded:
- brainstorming: Socratic design refinement before coding
- writing-plans: Break work into bite-sized tasks
- executing-plans: Batch execution with checkpoints
- subagent-driven-development: Two-stage review (spec + quality)
- test-driven-development: RED-GREEN-REFACTOR cycle
- systematic-debugging: 4-phase root cause process
- requesting-code-review: Pre-review checklist
- receiving-code-review: Respond to feedback
- dispatching-parallel-agents: Concurrent subagent workflows
- using-git-worktrees: Parallel development branches
- finishing-a-development-branch: Merge/PR decision workflow
- verification-before-completion: Ensure it's actually fixed
- writing-skills: Create new skills following best practices
- using-superpowers: Introduction to the skills system
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

SKILLS_PATH = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge\central_skills")


class SuperpowersSkill:
    """Represents a single Superpowers skill."""

    def __init__(self, name: str, skill_dir: Path):
        self.name = name
        self.skill_dir = skill_dir
        self.description = ""
        self.content = ""
        self.supporting_files: Dict[str, str] = {}
        self._load()

    def _load(self):
        """Load SKILL.md and supporting files."""
        skill_file = self.skill_dir / "SKILL.md"
        if not skill_file.exists():
            return

        raw = skill_file.read_text(encoding="utf-8")
        self.content = raw

        # Extract YAML frontmatter
        match = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.DOTALL)
        if match:
            header = match.group(1)
            self.content = match.group(2).strip()

            for line in header.split("\n"):
                line = line.strip()
                if line.startswith("description:"):
                    self.description = line.split(":", 1)[1].strip()
                elif line.startswith("name:"):
                    self.name = line.split(":", 1)[1].strip()

        # Load supporting files
        for f in self.skill_dir.iterdir():
            if f.name != "SKILL.md" and f.is_file():
                self.supporting_files[f.name] = f.read_text(encoding="utf-8")

    def get_prompt(self) -> str:
        """Get the full skill content as a system prompt."""
        parts = [f"# Skill: {self.name}", f"**Description**: {self.description}", "", self.content]

        for fname, fcontent in self.supporting_files.items():
            parts.append(f"\n--- Supporting File: {fname} ---\n{fcontent}")

        return "\n".join(parts)

    def is_relevant(self, task: str) -> bool:
        """Check if this skill is relevant to the given task."""
        task_lower = task.lower()
        content_lower = self.content.lower()
        desc_lower = self.description.lower()

        # Extract keywords from description (trigger words)
        trigger_words = []
        for word in re.findall(r"\b\w{4,}\b", desc_lower):
            if word not in ("when", "this", "that", "with", "from", "have", "been", "will", "skill", "using"):
                trigger_words.append(word)

        # Check if any trigger word appears in the task
        matches = sum(1 for w in trigger_words if w in task_lower)
        if matches >= 1:
            return True

        # Also check the content for strong keywords
        strong_keywords = {
            "brainstorming": ["design", "plan", "spec", "architecture", "approach", "build", "create", "implement"],
            "writing-plans": ["plan", "break down", "task", "implement", "steps"],
            "test-driven-development": ["test", "tdd", "red-green", "refactor", "unit test"],
            "systematic-debugging": ["bug", "debug", "error", "fix", "broken", "crash", "failing", "issue"],
            "subagent-driven-development": ["subagent", "parallel", "dispatch", "multiple tasks"],
            "requesting-code-review": ["review", "check", "verify", "quality"],
            "receiving-code-review": ["feedback", "review comment", "fix review"],
            "executing-plans": ["execute", "implement plan", "follow plan"],
            "using-git-worktrees": ["branch", "worktree", "parallel", "isolate"],
            "finishing-a-development-branch": ["finish", "merge", "pr", "branch complete"],
            "dispatching-parallel-agents": ["parallel", "concurrent", "multiple agents"],
            "verification-before-completion": ["verify", "confirm", "complete", "done", "finished"],
            "writing-skills": ["skill", "create skill", "write skill"],
            "using-superpowers": ["superpowers", "skill system"],
        }

        keywords = strong_keywords.get(self.name, [])
        if any(kw in task_lower for kw in keywords):
            return True

        return False


class SuperpowersLoader:
    """Loads and manages all Superpowers skills."""

    def __init__(self, skills_path: Optional[Path] = None):
        self.skills_path = skills_path or SKILLS_PATH
        self.skills: Dict[str, SuperpowersSkill] = {}
        self._load_all()

    def _load_all(self):
        """Load all skills from the skills directory."""
        if not self.skills_path.exists():
            print(f"[SuperpowersLoader] Skills path not found: {self.skills_path}")
            return

        for skill_dir in sorted(self.skills_path.iterdir()):
            if not skill_dir.is_dir():
                continue
            if not (skill_dir / "SKILL.md").exists():
                continue

            skill = SuperpowersSkill(skill_dir.name, skill_dir)
            self.skills[skill.name] = skill
            print(f"[SuperpowersLoader] Loaded skill: {skill.name}")

        print(f"[SuperpowersLoader] {len(self.skills)} skills loaded")

    def find_relevant_skills(self, task: str) -> List[Dict]:
        """Find skills relevant to the given task."""
        relevant = []
        for name, skill in self.skills.items():
            if skill.is_relevant(task):
                relevant.append({
                    "name": name,
                    "description": skill.description,
                    "prompt": skill.get_prompt()[:2000],
                })
        return relevant

    def get_skill(self, name: str) -> Optional[SuperpowersSkill]:
        """Get a specific skill by name."""
        return self.skills.get(name)

    def list_skills(self) -> List[Dict]:
        """List all available skills."""
        return [
            {"name": s.name, "description": s.description, "files": len(s.supporting_files)}
            for s in self.skills.values()
        ]

    def build_system_prompt(self, task: str) -> str:
        """Build an enhanced system prompt with relevant skills."""
        relevant = self.find_relevant_skills(task)
        if not relevant:
            return ""

        parts = ["# Active Superpowers Skills\n"]
        for skill in relevant:
            parts.append(f"## {skill['name']}")
            parts.append(skill['description'])
            parts.append("")
            parts.append(skill['prompt'][:3000])
            parts.append("")

        return "\n".join(parts)


def load_superpowers(skills_path=None) -> SuperpowersLoader:
    """Factory function."""
    return SuperpowersLoader(skills_path)


if __name__ == "__main__":
    loader = load_superpowers()

    print("\n=== All Skills ===")
    for s in loader.list_skills():
        print(f"  - {s['name']}: {s['description'][:80]}")

    test_tasks = [
        "Build a REST API for user management",
        "Debug why the login endpoint returns 500",
        "Write tests for the payment module",
        "Plan a new feature for real-time notifications",
        "Review this PR for security issues",
    ]

    print("\n=== Skill Matching ===")
    for task in test_tasks:
        relevant = loader.find_relevant_skills(task)
        print(f"\nTask: \"{task}\"")
        if relevant:
            for s in relevant:
                print(f"  → {s['name']}: {s['description']}")
        else:
            print("  → No matching skills")
