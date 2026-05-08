import os
import re
import json
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

from knowledge_graph import KnowledgeGraph, _normalize
from sync_tracker import get_sync_tracker


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


class PalaceMiner:
    """
    Automatically populates the MemPalace from existing vault files and project directories.

    Mines three sources:
    1. Vault (markdown files) — creates wings from folders/tags, rooms from files/headers
    2. Projects (directories) — creates wings from projects, rooms from components
    3. Memory SQLite — creates entities from categories, adds triples from facts

    Uses content hashing to skip unchanged files on re-mine (MegaMem-inspired).
    """

    def __init__(self, vault_path=None, project_paths=None, memory_sqlite_path=None):
        self.vault_path = Path(vault_path) if vault_path else None
        self.project_paths = [Path(p) for p in project_paths] if project_paths else []
        self.memory_sqlite_path = Path(memory_sqlite_path) if memory_sqlite_path else None

        self.kg = KnowledgeGraph()
        self.sync = get_sync_tracker()
        self.gemini = None
        self._init_gemini()
        self._stats = {
            "vault_files_processed": 0,
            "vault_files_skipped": 0,
            "project_files_processed": 0,
            "project_files_skipped": 0,
            "memory_entries_processed": 0,
            "total_triples": 0,
        }

    def _init_gemini(self):
        try:
            config_path = Path(r"%USERPROFILE%\Desktop\AI projects\Mark-XXXIX\config\api_keys.json")
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    api_key = json.load(f).get("gemini_api_key")
                if api_key:
                    from google import genai
                    self.gemini = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
        except Exception as e:
            print(f"[PalaceMiner] ⚠️ Gemini init failed: {e}")

    def mine_vault(self, vault_path) -> Dict[str, Any]:
        vault = Path(vault_path) if vault_path else self.vault_path
        if not vault or not vault.exists():
            return {"wings_created": 0, "rooms_created": 0, "triples_added": 0, "files_skipped": 0}

        wings_created = set()
        rooms_created = set()
        triples_added = 0
        files_skipped = 0

        md_files = list(vault.rglob("*.md"))

        for md_file in md_files:
            rel_path = md_file.relative_to(vault).as_posix()

            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            if not self.sync.should_mine("vault", rel_path, content):
                files_skipped += 1
                continue

            self._stats["vault_files_processed"] += 1
            file_triples = 0

            folder = md_file.parent.name
            file_stem = md_file.stem

            wing_name = f"wing_{_normalize(folder)}"
            wings_created.add(wing_name)
            self.kg.add_triple(wing_name, "type", "wing", source="vault_miner")
            self.kg.add_triple(wing_name, "label", folder, source="vault_miner")
            file_triples += 2

            room_name = f"room_{_normalize(file_stem)}"
            rooms_created.add(room_name)
            self.kg.add_triple(room_name, "type", "room", source="vault_miner")
            self.kg.add_triple(room_name, "label", file_stem, source="vault_miner")
            file_triples += 2

            self.kg.add_triple(wing_name, "contains", room_name, source="vault_miner")
            file_triples += 1

            frontmatter = self._extract_frontmatter(content)
            tags = frontmatter.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.strip("[]").split(",") if t.strip()]

            for tag in tags:
                tag_wing = f"wing_tag_{_normalize(tag)}"
                wings_created.add(tag_wing)
                self.kg.add_triple(tag_wing, "type", "wing", source="vault_miner")
                self.kg.add_triple(room_name, "tagged", tag_wing, source="vault_miner")
                file_triples += 2

            headers = self._extract_headers(content)
            for header in headers:
                header_room = f"room_{_normalize(header)}"
                rooms_created.add(header_room)
                self.kg.add_triple(header_room, "type", "room", source="vault_miner")
                self.kg.add_triple(room_name, "contains", header_room, source="vault_miner")
                file_triples += 2

            wikilinks = self._extract_wikilinks(content)
            for link in wikilinks:
                link_room = f"room_{_normalize(link)}"
                rooms_created.add(link_room)
                self.kg.add_triple(link_room, "type", "room", source="vault_miner")
                self.kg.add_triple(room_name, "links_to", link_room, source="vault_miner")
                file_triples += 2

            # LLM-powered entity/relationship extraction (Graphiti-inspired)
            llm_triples = self._extract_llm_triples(content, room_name)
            file_triples += llm_triples

            self.sync.mark_mined("vault", rel_path, content, triples_added=file_triples)
            triples_added += file_triples

        self._stats["vault_files_skipped"] += files_skipped
        self._stats["total_triples"] += triples_added
        return {
            "wings_created": len(wings_created),
            "rooms_created": len(rooms_created),
            "triples_added": triples_added,
            "files_skipped": files_skipped,
        }

    def mine_projects(self, project_paths) -> Dict[str, Any]:
        paths = [Path(p) for p in project_paths] if project_paths else self.project_paths
        if not paths:
            return {"wings_created": 0, "rooms_created": 0, "triples_added": 0, "files_skipped": 0}

        wings_created = set()
        rooms_created = set()
        triples_added = 0
        files_skipped = 0

        key_files = [
            "README.md", "README.rst", "README.txt",
            "main.py", "app.py", "index.js", "index.ts",
            "package.json", "requirements.txt", "pyproject.toml",
            "Cargo.toml", "go.mod", "setup.py", "Makefile",
        ]

        for proj_path in paths:
            if not proj_path.exists():
                continue

            proj_name = proj_path.name
            wing_name = f"wing_proj_{_normalize(proj_name)}"
            wings_created.add(wing_name)
            self.kg.add_triple(wing_name, "type", "wing", source="project_miner")
            self.kg.add_triple(wing_name, "label", proj_name, source="project_miner")
            self.kg.add_triple(wing_name, "path", str(proj_path), source="project_miner")
            triples_added += 3

            for key_file in key_files:
                fp = proj_path / key_file
                if not fp.exists():
                    continue

                rel_path = fp.relative_to(proj_path.parent).as_posix()
                try:
                    content = fp.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                if not self.sync.should_mine("project", rel_path, content):
                    files_skipped += 1
                    continue

                self._stats["project_files_processed"] += 1
                file_triples = 0

                room_name = f"room_{_normalize(key_file)}"
                rooms_created.add(room_name)
                self.kg.add_triple(room_name, "type", "room", source="project_miner")
                self.kg.add_triple(wing_name, "contains", room_name, source="project_miner")
                file_triples += 2

                content_limited = content[:2000]

                if key_file == "package.json":
                    try:
                        pkg = json.loads(content_limited)
                        deps = list(pkg.get("dependencies", {}).keys())[:10]
                        for dep in deps:
                            dep_room = f"room_dep_{_normalize(dep)}"
                            rooms_created.add(dep_room)
                            self.kg.add_triple(dep_room, "type", "room", source="project_miner")
                            self.kg.add_triple(room_name, "depends_on", dep_room, source="project_miner")
                            file_triples += 2
                    except Exception:
                        pass

                elif key_file == "requirements.txt":
                    for line in content_limited.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            dep = line.split("==")[0].split(">=")[0].strip()
                            dep_room = f"room_dep_{_normalize(dep)}"
                            rooms_created.add(dep_room)
                            self.kg.add_triple(dep_room, "type", "room", source="project_miner")
                            self.kg.add_triple(room_name, "depends_on", dep_room, source="project_miner")
                            file_triples += 2

                self.sync.mark_mined("project", rel_path, content, triples_added=file_triples)
                triples_added += file_triples

            py_files = list(proj_path.rglob("*.py"))[:20]
            for py_file in py_files:
                mod_name = py_file.stem
                room_name = f"room_mod_{_normalize(mod_name)}"
                rooms_created.add(room_name)
                self.kg.add_triple(room_name, "type", "room", source="project_miner")
                self.kg.add_triple(wing_name, "contains", room_name, source="project_miner")
                triples_added += 2

        self._stats["project_files_skipped"] += files_skipped
        self._stats["total_triples"] += triples_added
        return {
            "wings_created": len(wings_created),
            "rooms_created": len(rooms_created),
            "triples_added": triples_added,
            "files_skipped": files_skipped,
        }

    def mine_memory(self, memory_sqlite_path) -> Dict[str, Any]:
        db_path = Path(memory_sqlite_path) if memory_sqlite_path else self.memory_sqlite_path
        if not db_path or not db_path.exists():
            return {"wings_created": 0, "rooms_created": 0, "triples_added": 0}

        wings_created = set()
        rooms_created = set()
        triples_added = 0

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        try:
            cur = conn.execute("SELECT DISTINCT category FROM memory_entries")
            categories = [r["category"] for r in cur.fetchall()]
        except Exception:
            categories = []

        for cat in categories:
            wing_name = f"wing_cat_{_normalize(cat)}"
            wings_created.add(wing_name)
            self.kg.add_triple(wing_name, "type", "wing", source="memory_miner")
            self.kg.add_triple(wing_name, "label", cat, source="memory_miner")
            triples_added += 2

        try:
            cur = conn.execute(
                "SELECT agent, key, value, category FROM memory_entries LIMIT 500"
            )
            entries = cur.fetchall()
        except Exception:
            entries = []

        self._stats["memory_entries_processed"] += len(entries)

        for entry in entries:
            agent = entry["agent"]
            key = entry["key"]
            value = entry["value"]
            category = entry["category"]

            agent_wing = f"wing_agent_{_normalize(agent)}"
            wings_created.add(agent_wing)
            self.kg.add_triple(agent_wing, "type", "wing", source="memory_miner")
            triples_added += 1

            key_room = f"room_{_normalize(key)}"
            rooms_created.add(key_room)
            self.kg.add_triple(key_room, "type", "room", source="memory_miner")
            triples_added += 1

            self.kg.add_triple(agent_wing, "knows", key_room, source="memory_miner")
            triples_added += 1

            if category:
                cat_wing = f"wing_cat_{_normalize(category)}"
                self.kg.add_triple(key_room, "category", cat_wing, source="memory_miner")
                triples_added += 1

        conn.close()
        self._stats["total_triples"] += triples_added
        return {
            "wings_created": len(wings_created),
            "rooms_created": len(rooms_created),
            "triples_added": triples_added,
        }

    def auto_mine_all(self) -> Dict[str, Any]:
        vault_result = self.mine_vault(self.vault_path) if self.vault_path else {"wings_created": 0, "rooms_created": 0, "triples_added": 0, "files_skipped": 0}
        project_result = self.mine_projects(self.project_paths) if self.project_paths else {"wings_created": 0, "rooms_created": 0, "triples_added": 0, "files_skipped": 0}
        memory_result = self.mine_memory(self.memory_sqlite_path) if self.memory_sqlite_path else {"wings_created": 0, "rooms_created": 0, "triples_added": 0}

        return {
            "vault": vault_result,
            "projects": project_result,
            "memory": memory_result,
            "total_wings": vault_result["wings_created"] + project_result["wings_created"] + memory_result["wings_created"],
            "total_rooms": vault_result["rooms_created"] + project_result["rooms_created"] + memory_result["rooms_created"],
            "total_triples": vault_result["triples_added"] + project_result["triples_added"] + memory_result["triples_added"],
            "files_skipped": vault_result.get("files_skipped", 0) + project_result.get("files_skipped", 0),
        }

    def get_mining_status(self) -> Dict[str, Any]:
        kg_stats = self.kg.stats()
        sync_stats = self.sync.get_stats()
        return {
            "vault_files_processed": self._stats["vault_files_processed"],
            "vault_files_skipped": self._stats["vault_files_skipped"],
            "project_files_processed": self._stats["project_files_processed"],
            "project_files_skipped": self._stats["project_files_skipped"],
            "memory_entries_processed": self._stats["memory_entries_processed"],
            "total_triples": self._stats["total_triples"] + kg_stats.get("triple_count", 0),
            "sync_state": sync_stats,
        }

    def reset_sync(self, source_type=None):
        """Reset sync state to force re-mine all files."""
        self.sync.reset_all(source_type)

    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        fm = {}
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if match:
            lines = match.group(1).splitlines()
            for line in lines:
                if ":" in line:
                    key, val = line.split(":", 1)
                    fm[key.strip()] = val.strip()
        return fm

    def _extract_headers(self, content: str) -> List[str]:
        headers = []
        for line in content.splitlines():
            m = re.match(r"^(#{1,6})\s+(.+)", line)
            if m:
                headers.append(m.group(2).strip())
        return headers

    def _extract_wikilinks(self, content: str) -> List[str]:
        return [m.group(1) for m in re.finditer(r"\[\[([^\]]+)\]\]", content)]

    def _extract_llm_triples(self, content: str, source_room: str) -> int:
        """Use Gemini to extract entity relationships from vault content (Graphiti-inspired).
        Returns number of triples added."""
        if not self.gemini:
            return 0

        # Limit content to avoid token overload
        content_limited = content[:4000]
        triples_added = 0

        try:
            prompt = (
                "Extract key entities and their relationships from this markdown note. "
                "Return ONLY a JSON array of objects with keys: 'entity', 'relation', 'target'. "
                "Examples:\n"
                '[{"entity": "Project X", "relation": "uses", "target": "Python"},\n'
                ' {"entity": "Kai", "relation": "contributed_to", "target": "memory system"}]\n\n'
                "Focus on: people, projects, technologies, tools, and their relationships.\n"
                "Keep entity names short (1-3 words). Use snake_case for relations.\n\n"
                f"Note content:\n{content_limited}\n\nReturn only the JSON array."
            )
            response = self.gemini.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
            if response.text:
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    for item in parsed[:15]:  # Cap at 15 triples per file
                        if all(k in item for k in ("entity", "relation", "target")):
                            entity = _normalize(str(item["entity"])[:50])
                            relation = str(item["relation"])[:50].replace(" ", "_")
                            target = str(item["target"])[:200]
                            if entity and relation and target:
                                self.kg.add_triple(entity, relation, target, source="llm_extraction")
                                self.kg.add_triple(source_room, "mentions", entity, source="llm_extraction")
                                triples_added += 2
        except Exception as e:
            print(f"[PalaceMiner] ⚠️ LLM extraction failed: {e}")

        return triples_added
