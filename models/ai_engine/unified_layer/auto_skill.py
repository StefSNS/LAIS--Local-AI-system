"""
Auto-Skill Generation v1.0 - Post-task SKILL.md synthesis.
Based on Hermes Agent auto-skill creation pattern.
Generates reusable SKILL.md files after complex tasks complete successfully.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
import json


SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)


class SkillTemplate:
    """Template for auto-generated SKILL.md files."""

    def __init__(
        self,
        name: str,
        category: str,
        description: str,
        steps: list[str],
        examples: list[str],
        triggers: list[str],
        metadata: Optional[dict] = None,
    ):
        self.name = name
        self.category = category
        self.description = description
        self.steps = steps
        self.examples = examples
        self.triggers = triggers
        self.metadata = metadata or {}
        self.created_at = datetime.now()

    def render(self) -> str:
        steps_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(self.steps))
        examples_text = "\n".join(f"- {ex}" for ex in self.examples)
        triggers_text = ", ".join(self.triggers)

        metadata_json = json.dumps(self.metadata, indent=2) if self.metadata else "{}"

        return f"""# Skill: {self.name}

**Category:** {self.category}
**Description:** {self.description}
**Triggers:** {triggers_text}
**Created:** {self.created_at.isoformat()}

## When to Use
{self.description}

## Steps
{steps_text}

## Examples
{examples_text}

## Notes
- Auto-generated skill based on successful task execution
- Review and refine before relying on for critical operations

## Metadata
```json
{metadata_json}
```
"""


class AutoSkillGenerator:
    """
    Analyzes task execution and generates reusable SKILL.md files.
    """

    def __init__(self, skills_dir: Path = SKILLS_DIR):
        self.skills_dir = skills_dir
        self._generated_count = 0

    def generate_from_task(
        self,
        task_description: str,
        task_result: str,
        task_steps: Optional[list[str]] = None,
        category: str = "general",
        confidence_threshold: float = 0.7,
    ) -> Optional[str]:
        if not task_description or not task_result:
            return None

        if len(task_result) < 50:
            return None

        name = self._extract_skill_name(task_description)
        steps = task_steps or self._extract_steps(task_result)
        examples = self._extract_examples(task_result)
        triggers = self._extract_triggers(task_description)

        if not steps:
            return None

        template = SkillTemplate(
            name=name,
            category=category,
            description=task_description,
            steps=steps,
            examples=examples[:5],
            triggers=triggers,
            metadata={
                "auto_generated": True,
                "source_task": task_description,
                "result_length": len(task_result),
            },
        )

        return self._save_skill(template)

    def generate_from_conversation(
        self,
        conversation: list[dict],
        topic: str,
        category: str = "general",
    ) -> Optional[str]:
        if len(conversation) < 3:
            return None

        steps = []
        for msg in conversation:
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                extracted = self._extract_steps(content)
                steps.extend(extracted)

        if not steps:
            return None

        template = SkillTemplate(
            name=self._extract_skill_name(topic),
            category=category,
            description=topic,
            steps=steps[:10],
            examples=[],
            triggers=[topic.lower()],
            metadata={"auto_generated": True, "source": "conversation"},
        )

        return self._save_skill(template)

    def list_skills(self) -> list[dict]:
        skills = []
        for skill_file in self.skills_dir.glob("*.md"):
            content = skill_file.read_text(encoding="utf-8")
            name = skill_file.stem
            skills.append({
                "name": name,
                "path": str(skill_file),
                "size_bytes": skill_file.stat().st_size,
            })
        return skills

    def get_skill(self, name: str) -> Optional[str]:
        skill_path = self.skills_dir / f"{name}.md"
        if skill_path.exists():
            return skill_path.read_text(encoding="utf-8")
        return None

    def _save_skill(self, template: SkillTemplate) -> Optional[str]:
        filename = template.name.lower().replace(" ", "_").replace("/", "_") + ".md"
        filepath = self.skills_dir / filename

        try:
            filepath.write_text(template.render(), encoding="utf-8")
            self._generated_count += 1
            return str(filepath)
        except Exception as e:
            print(f"[AutoSkill] Failed to save skill: {e}")
            return None

    @staticmethod
    def _extract_skill_name(description: str) -> str:
        words = description.split()[:5]
        return " ".join(w.capitalize() for w in words)

    @staticmethod
    def _extract_steps(content: str) -> list[str]:
        import re
        steps = []
        numbered = re.findall(r'(?:^|\n)\s*\d+[.)]\s*(.+?)(?=\n\d+[.)]|\n\n|$)', content)
        if numbered:
            steps = [s.strip() for s in numbered]
        else:
            bullet = re.findall(r'(?:^|\n)\s*[-*]\s*(.+?)(?=\n[-*]|\n\n|$)', content)
            steps = [s.strip() for s in bullet]

        return [s for s in steps if len(s) > 10]

    @staticmethod
    def _extract_examples(content: str) -> list[str]:
        import re
        examples = re.findall(r'(?:example|for instance|such as)[:\s]*(.+?)(?:\n\n|$)', content, re.IGNORECASE)
        return [e.strip() for e in examples if len(e) > 20]

    @staticmethod
    def _extract_triggers(description: str) -> list[str]:
        import re
        words = re.findall(r'\b\w+\b', description.lower())
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                      "have", "has", "had", "do", "does", "did", "will", "would", "could",
                      "should", "may", "might", "can", "to", "of", "in", "for", "on", "with",
                      "at", "by", "from", "as", "into", "through", "during", "before", "after"}
        return [w for w in words if w not in stop_words and len(w) > 3]


_global_generator: Optional[AutoSkillGenerator] = None


def get_auto_skill_generator() -> AutoSkillGenerator:
    global _global_generator
    if _global_generator is None:
        _global_generator = AutoSkillGenerator()
    return _global_generator
