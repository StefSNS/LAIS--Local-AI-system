"""
Knowledge Files System - Project context injection.
Based on Codebuff's knowledge.md system.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

KNOWLEDGE_FILENAME = "knowledge.md"
AGENTS_DIR = ".agents"
AGENTS_TYPES_DIR = f"{AGENTS_DIR}/types"


@dataclass
class KnowledgeFile:
    """A knowledge file with content and metadata."""
    path: Path
    content: str
    project_root: Path
    loaded_at: str = field(default_factory=lambda: datetime.now().isoformat())
    auto_inject: bool = True


@dataclass
class ContextReference:
    """Reference to a file or section (e.g., @filename or @filename#section)."""
    name: str
    path: Optional[Path] = None
    section: Optional[str] = None
    line_range: Optional[tuple] = None


class KnowledgeFilesManager:
    """
    Manages knowledge.md files for project context injection.
    Similar to Codebuff's knowledge.md system.
    """

    def __init__(self):
        self.loaded_knowledge: Dict[str, KnowledgeFile] = {}
        self.current_project: Optional[Path] = None
        self.context_cache: Dict[str, str] = {}
        self.lock = Lock()

    def find_knowledge_file(self, project_root: Path) -> Optional[Path]:
        """Find knowledge.md in project root or ancestor directories."""
        search_path = project_root.resolve()
        while search_path != search_path.parent:
            knowledge_path = search_path / KNOWLEDGE_FILENAME
            if knowledge_path.exists():
                return knowledge_path
            search_path = search_path.parent
        return None

    def load_knowledge(self, project_root: Path, force: bool = False) -> Dict[str, Any]:
        """Load knowledge.md for a project."""
        project_key = str(project_root.resolve())

        if project_key in self.loaded_knowledge and not force:
            return {"success": True, "cached": True, "path": self.loaded_knowledge[project_key].path}

        knowledge_path = self.find_knowledge_file(project_root)
        if not knowledge_path:
            return {"success": False, "error": "No knowledge.md found"}

        try:
            with open(knowledge_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.loaded_knowledge[project_key] = KnowledgeFile(
                path=knowledge_path,
                content=content,
                project_root=project_root.resolve(),
            )
            self.current_project = project_root.resolve()

            return {
                "success": True,
                "path": str(knowledge_path),
                "content_preview": content[:200],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_knowledge_content(self, project_root: Path) -> Optional[str]:
        """Get loaded knowledge content for a project."""
        project_key = str(project_root.resolve())
        if project_key in self.loaded_knowledge:
            return self.loaded_knowledge[project_key].content
        return None

    def render_for_prompt(self, project_root: Path, max_length: int = 4000) -> str:
        """Render knowledge content for system prompt injection."""
        content = self.get_knowledge_content(project_root)
        if not content:
            return ""

        if len(content) > max_length:
            content = content[:max_length] + "\n\n[...] (truncated)"

        return f"""\
══════════════════════════════════════════════════
PROJECT KNOWLEDGE
══════════════════════════════════════════════════
{content}
"""

    def parse_mentions(self, text: str) -> List[ContextReference]:
        """
        Parse @mentions in text.
        Supports: @filename, @filename#section, @filename:line-range
        """
        mentions = []
        pattern = r'@([^\s#:]+)(?:#([^\s:]+))?(?::(\d+-\d+))?'

        for match in re.finditer(pattern, text):
            name = match.group(1)
            section = match.group(2)
            line_range = match.group(3)

            ref = ContextReference(
                name=name,
                section=section,
            )

            if line_range:
                parts = line_range.split("-")
                ref.line_range = (int(parts[0]), int(parts[1]))

            mentions.append(ref)

        return mentions

    def resolve_mention(self, ref: ContextReference, project_root: Path) -> Optional[str]:
        """Resolve a @mention to actual content."""
        search_paths = [
            project_root / ref.name,
            project_root / "src" / ref.name,
            project_root / "lib" / ref.name,
            project_root / "app" / ref.name,
        ]

        for path in search_paths:
            if path.exists() and path.is_file():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if ref.section:
                        lines = content.split("\n")
                        found = False
                        result_lines = []
                        for line in lines:
                            if ref.section.lower() in line.lower():
                                found = True
                            if found:
                                result_lines.append(line)
                        if result_lines:
                            return "\n".join(result_lines[:50])

                    if ref.line_range:
                        lines = content.split("\n")
                        start, end = ref.line_range
                        return "\n".join(lines[start-1:end])

                    return content[:2000]
                except Exception:
                    pass

        return None

    def get_context_for_mentions(self, text: str, project_root: Path) -> Dict[str, str]:
        """Get context for all @mentions in text."""
        mentions = self.parse_mentions(text)
        context = {}

        for ref in mentions:
            content = self.resolve_mention(ref, project_root)
            if content:
                context[ref.name] = content

        return context

    def create_starter_knowledge(self, project_root: Path) -> Dict[str, Any]:
        """Create a starter knowledge.md file."""
        knowledge_path = project_root / KNOWLEDGE_FILENAME

        if knowledge_path.exists():
            return {"success": False, "error": "knowledge.md already exists"}

        starter_content = """\
# Project Knowledge

## Project Overview
<!-- Briefly describe your project -->

## Tech Stack
- Language:
- Framework:
- Dependencies:

## Key Files
<!-- Important files and their purposes -->

## Common Patterns
<!-- Coding conventions, patterns used -->

## Important Notes
<!-- Any important context for the AI agent -->

## Recent Changes
<!-- Recent work that the agent should know about -->
"""

        try:
            with open(knowledge_path, "w", encoding="utf-8") as f:
                f.write(starter_content)

            return {"success": True, "path": str(knowledge_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def unload_knowledge(self, project_root: Path) -> bool:
        """Unload knowledge for a project."""
        project_key = str(project_root.resolve())
        if project_key in self.loaded_knowledge:
            del self.loaded_knowledge[project_key]
            return True
        return False

    def get_loaded_projects(self) -> List[str]:
        """Get list of projects with loaded knowledge."""
        return list(self.loaded_knowledge.keys())


_knowledge_manager_instance: Optional[KnowledgeFilesManager] = None


def get_knowledge_manager() -> KnowledgeFilesManager:
    """Get or create the knowledge files manager instance."""
    global _knowledge_manager_instance
    if _knowledge_manager_instance is None:
        _knowledge_manager_instance = KnowledgeFilesManager()
    return _knowledge_manager_instance


if __name__ == "__main__":
    km = get_knowledge_manager()

    print("=== Knowledge Files Manager ===")

    test_path = Path(__file__).resolve().parent.parent.parent.parent.parent

    print("\n--- Load Knowledge ---")
    result = km.load_knowledge(test_path)
    print(f"Load: {result}")

    print("\n--- Render for Prompt ---")
    prompt_content = km.render_for_prompt(test_path)
    if prompt_content:
        print(prompt_content[:300])
    else:
        print("No knowledge file found")

    print("\n--- Parse Mentions ---")
    test_text = "Check @config.ts and @main.py#init for details, also look at @utils.ts:10-20"
    mentions = km.parse_mentions(test_text)
    for m in mentions:
        print(f"  {m.name} (section: {m.section}, lines: {m.line_range})")

    print("\n--- Create Starter ---")
    starter_result = km.create_starter_knowledge(Path(tempfile.gettempdir()) / "test_project")
    print(f"Create: {starter_result}")