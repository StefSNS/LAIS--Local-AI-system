"""
Prompt Library v1.0
Prompt crafting, testing, versioning, and optimization system.
Based on prompt engineering best practices and Langfuse prompt management.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


PROMPT_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "prompts"
PROMPT_DIR.mkdir(parents=True, exist_ok=True)
LIBRARY_FILE = PROMPT_DIR / "library.json"


class Prompt:
    """A single prompt template with versioning."""

    def __init__(
        self,
        name: str,
        template: str,
        category: str = "general",
        tags: list[str] = None,
        system_prompt: str = "",
        version: int = 1,
        description: str = "",
        variables: list[str] = None,
    ):
        self.name = name
        self.template = template
        self.category = category
        self.tags = tags or []
        self.system_prompt = system_prompt
        self.version = version
        self.description = description
        self.variables = variables or self._extract_variables()
        self.created = datetime.now()
        self.usage_count = 0
        self.avg_score = 0.0

    def _extract_variables(self) -> list[str]:
        return list(set(re.findall(r'\{(\w+)\}', self.template)))

    def render(self, **kwargs) -> str:
        result = self.template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "template": self.template,
            "category": self.category,
            "tags": self.tags,
            "system_prompt": self.system_prompt,
            "version": self.version,
            "description": self.description,
            "variables": self.variables,
            "created": self.created.isoformat(),
            "usage_count": self.usage_count,
            "avg_score": round(self.avg_score, 3),
        }


class PromptLibrary:
    """
    Prompt management system.
    Supports: CRUD, versioning, search by tag/category, usage tracking.
    """

    def __init__(self):
        self._prompts: dict[str, Prompt] = {}
        self._history: list[dict] = []
        self._load()
        self._add_defaults()

    def add_prompt(
        self,
        name: str,
        template: str,
        category: str = "general",
        tags: list[str] = None,
        system_prompt: str = "",
        description: str = "",
    ) -> Prompt:
        existing = self._prompts.get(name)
        version = (existing.version + 1) if existing else 1

        prompt = Prompt(
            name=name,
            template=template,
            category=category,
            tags=tags,
            system_prompt=system_prompt,
            version=version,
            description=description,
        )
        if existing:
            prompt.usage_count = existing.usage_count
            prompt.avg_score = existing.avg_score

        self._prompts[name] = prompt
        self._save()
        return prompt

    def get_prompt(self, name: str) -> Optional[Prompt]:
        return self._prompts.get(name)

    def delete_prompt(self, name: str) -> bool:
        if name in self._prompts:
            del self._prompts[name]
            self._save()
            return True
        return False

    def render(self, prompt_name: str, **kwargs) -> Optional[str]:
        prompt = self._prompts.get(prompt_name)
        if not prompt:
            return None
        prompt.usage_count += 1
        self._save()
        return prompt.render(**kwargs)

    def search(self, query: str = "", category: str = None, tag: str = None) -> list[dict]:
        results = list(self._prompts.values())

        if query:
            query_lower = query.lower()
            results = [p for p in results if query_lower in p.name.lower() or query_lower in p.description.lower() or query_lower in p.template.lower()]
        if category:
            results = [p for p in results if p.category == category]
        if tag:
            results = [p for p in results if tag in p.tags]

        return [p.to_dict() for p in results]

    def get_by_category(self, category: str) -> list[dict]:
        return [p.to_dict() for p in self._prompts.values() if p.category == category]

    def get_by_tag(self, tag: str) -> list[dict]:
        return [p.to_dict() for p in self._prompts.values() if tag in p.tags]

    def record_feedback(self, name: str, score: float, feedback: str = "") -> None:
        prompt = self._prompts.get(name)
        if not prompt:
            return
        prompt.avg_score = ((prompt.avg_score * (prompt.usage_count - 1)) + score) / prompt.usage_count if prompt.usage_count > 0 else score
        self._history.append({
            "prompt": name,
            "score": score,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

    def get_top_prompts(self, n: int = 10) -> list[dict]:
        sorted_prompts = sorted(self._prompts.values(), key=lambda p: p.avg_score, reverse=True)
        return [p.to_dict() for p in sorted_prompts[:n]]

    def get_most_used(self, n: int = 10) -> list[dict]:
        sorted_prompts = sorted(self._prompts.values(), key=lambda p: p.usage_count, reverse=True)
        return [p.to_dict() for p in sorted_prompts[:n]]

    def export(self) -> str:
        return json.dumps({name: p.to_dict() for name, p in self._prompts.items()}, indent=2)

    def list_all(self) -> list[dict]:
        return [p.to_dict() for p in self._prompts.values()]

    def stats(self) -> dict:
        categories = {}
        for p in self._prompts.values():
            if p.category not in categories:
                categories[p.category] = 0
            categories[p.category] += 1

        return {
            "total_prompts": len(self._prompts),
            "categories": categories,
            "total_usage": sum(p.usage_count for p in self._prompts.values()),
            "history_entries": len(self._history),
        }

    def _load(self) -> None:
        if LIBRARY_FILE.exists():
            try:
                data = json.loads(LIBRARY_FILE.read_text(encoding="utf-8"))
                for p_data in data.get("prompts", {}).values():
                    prompt = Prompt(
                        name=p_data["name"],
                        template=p_data["template"],
                        category=p_data.get("category", "general"),
                        tags=p_data.get("tags", []),
                        system_prompt=p_data.get("system_prompt", ""),
                        version=p_data.get("version", 1),
                        description=p_data.get("description", ""),
                        variables=p_data.get("variables", []),
                    )
                    prompt.usage_count = p_data.get("usage_count", 0)
                    prompt.avg_score = p_data.get("avg_score", 0.0)
                    if "created" in p_data:
                        prompt.created = datetime.fromisoformat(p_data["created"])
                    self._prompts[prompt.name] = prompt
                self._history = data.get("history", [])
            except Exception:
                pass

    def _save(self) -> None:
        try:
            data = {
                "prompts": {name: p.to_dict() for name, p in self._prompts.items()},
                "history": self._history[-100:],
            }
            LIBRARY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _add_defaults(self) -> None:
        if not self._prompts:
            defaults = [
                {
                    "name": "summarize_text",
                    "template": "Summarize the following text in {num_sentences} sentences:\n\n{text}",
                    "category": "summarization",
                    "tags": ["summary", "compression"],
                    "description": "Summarize text to a specific number of sentences",
                },
                {
                    "name": "extract_keywords",
                    "template": "Extract the top {top_n} keywords from the following text:\n\n{text}",
                    "category": "extraction",
                    "tags": ["keywords", "nlp"],
                    "description": "Extract key terms from text",
                },
                {
                    "name": "code_review",
                    "template": "Review the following {language} code for bugs, security issues, and improvements:\n\n{code}",
                    "category": "code",
                    "tags": ["review", "security", "quality"],
                    "description": "Code review prompt",
                },
                {
                    "name": "daily_journal",
                    "template": "Write a journal entry for {date}. Key topics: {topics}. Mood: {mood}.",
                    "category": "journal",
                    "tags": ["daily", "reflection"],
                    "description": "Daily journal template",
                },
                {
                    "name": "research_query",
                    "template": "Research the topic: {topic}. Focus areas: {focus}. Provide structured findings with sources.",
                    "category": "research",
                    "tags": ["research", "analysis"],
                    "description": "Research query template",
                },
                {
                    "name": "meeting_notes",
                    "template": "Meeting notes for {meeting_name} on {date}.\nAttendees: {attendees}\nAgenda: {agenda}\n\nDecisions:\n{decisions}\n\nAction items:\n{actions}",
                    "category": "notes",
                    "tags": ["meeting", "collaboration"],
                    "description": "Meeting notes template",
                },
            ]
            for d in defaults:
                self.add_prompt(**d)


_global_prompt_library: Optional[PromptLibrary] = None


def get_prompt_library() -> PromptLibrary:
    global _global_prompt_library
    if _global_prompt_library is None:
        _global_prompt_library = PromptLibrary()
    return _global_prompt_library
