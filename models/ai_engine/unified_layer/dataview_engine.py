"""
Dataview Query Language (DQL) v1.0
SQL-like query engine over Markdown vault metadata.
Based on Obsidian Dataview patterns.
Supports: LIST, TABLE, TASK queries with FROM, WHERE, SORT, GROUP, LIMIT.
"""

import re
from pathlib import Path
from typing import Optional, Any


class VaultIndex:
    """Indexes all Markdown files and their YAML frontmatter metadata."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.files = {}
        self._build_index()

    def _build_index(self) -> None:
        if not self.vault_path.exists():
            return
        for md_file in self.vault_path.rglob("*.md"):
            rel = str(md_file.relative_to(self.vault_path))
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            metadata = self._parse_metadata(content, md_file, rel)
            self.files[rel] = metadata

    def _parse_metadata(self, content: str, file_path: Path, rel_path: str) -> dict:
        metadata = {
            "file": rel_path,
            "path": rel_path,
            "name": file_path.stem,
            "title": file_path.stem.replace("_", " ").replace("-", " ").title(),
            "folder": file_path.parent.name,
            "full_path": str(file_path),
            "size": file_path.stat().st_size if file_path.exists() else 0,
            "tags": [],
            "links": [],
            "tasks": [],
            "created": None,
            "modified": None,
            "word_count": 0,
        }

        if file_path.exists():
            import datetime
            stat = file_path.stat()
            metadata["created"] = datetime.datetime.fromtimestamp(stat.st_ctime).isoformat()
            metadata["modified"] = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()

        words = content.split()
        metadata["word_count"] = len(words)

        yaml_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if yaml_match:
            try:
                import yaml
                frontmatter = yaml.safe_load(yaml_match.group(1))
                if isinstance(frontmatter, dict):
                    metadata.update(frontmatter)
            except Exception:
                for line in yaml_match.group(1).split("\n"):
                    if ":" in line:
                        key, _, val = line.partition(":")
                        metadata[key.strip()] = val.strip().strip('"').strip("'")

        metadata["tags"] = re.findall(r'#(\w+)', content)
        metadata["links"] = re.findall(r'\[\[([^\]]+)\]\]', content)
        metadata["inlinks"] = []

        tasks = re.findall(r'- \[([ xX])\]\s+(.*)', content)
        metadata["tasks"] = [{"completed": c in "xX", "text": t.strip()} for c, t in tasks]

        inline_fields = re.findall(r'\[(\w+)::\s*([^\]]+)\]', content)
        for key, val in inline_fields:
            metadata[key] = val.strip()

        return metadata

    def refresh(self) -> None:
        self._build_index()

    def get_all_files(self) -> list[dict]:
        return list(self.files.values())

    def get_file(self, path: str) -> Optional[dict]:
        return self.files.get(path)


class DQLParser:
    """Parses Dataview Query Language strings."""

    def __init__(self, query: str):
        self.query = query.strip()
        self.query_type = "LIST"
        self.fields = []
        self.source = None
        self.where_clauses = []
        self.sort_by = None
        self.sort_desc = False
        self.group_by = None
        self.limit = None

    def parse(self) -> dict:
        lines = self.query.split("\n")
        first_line = lines[0].strip().upper()

        if first_line.startswith("TABLE"):
            self.query_type = "TABLE"
            field_str = first_line[5:].strip()
            if field_str:
                self.fields = [f.strip() for f in field_str.split(",")]
        elif first_line.startswith("TASK"):
            self.query_type = "TASK"
        elif first_line.startswith("CALENDAR"):
            self.query_type = "CALENDAR"
            parts = first_line.split()
            if len(parts) > 1:
                self.fields = [parts[1]]
        elif first_line.startswith("LIST"):
            self.query_type = "LIST"
            parts = first_line.split()
            if len(parts) > 1:
                self.fields = [parts[1]]

        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            upper = line.upper()
            if upper.startswith("FROM "):
                self.source = line[5:].strip()
            elif upper.startswith("WHERE "):
                self.where_clauses.append(line[6:].strip())
            elif upper.startswith("SORT "):
                sort_str = line[5:].strip()
                parts = sort_str.split()
                self.sort_by = parts[0]
                self.sort_desc = len(parts) > 1 and parts[1].upper() == "DESC"
            elif upper.startswith("GROUP BY "):
                self.group_by = line[9:].strip()
            elif upper.startswith("LIMIT "):
                try:
                    self.limit = int(line[6:].strip())
                except ValueError:
                    pass

        return {
            "query_type": self.query_type,
            "fields": self.fields,
            "source": self.source,
            "where_clauses": self.where_clauses,
            "sort_by": self.sort_by,
            "sort_desc": self.sort_desc,
            "group_by": self.group_by,
            "limit": self.limit,
        }


class DQLEvaluator:
    """Evaluates parsed DQL queries against a vault index."""

    def __init__(self, index: VaultIndex):
        self.index = index

    def execute(self, parsed: dict) -> list[dict]:
        files = self.index.get_all_files()

        if parsed["source"]:
            files = self._apply_source(files, parsed["source"])

        for clause in parsed["where_clauses"]:
            files = self._apply_where(files, clause)

        if parsed["sort_by"]:
            files = self._apply_sort(files, parsed["sort_by"], parsed["sort_desc"])

        if parsed["group_by"]:
            files = self._apply_group(files, parsed["group_by"])

        if parsed["limit"] is not None:
            files = files[:parsed["limit"]]

        return files

    def _apply_source(self, files: list[dict], source: str) -> list[dict]:
        source = source.strip()
        if source.startswith('"') and source.endswith('"'):
            folder = source.strip('"')
            return [f for f in files if folder in f.get("path", "")]
        if source.startswith("#"):
            tag = source[1:]
            return [f for f in files if tag in f.get("tags", [])]
        if source.startswith("tag:"):
            tag = source[4:]
            return [f for f in files if tag in f.get("tags", [])]
        if source.startswith("-"):
            exclude = source[1:]
            if exclude.startswith("#"):
                tag = exclude[1:]
                return [f for f in files if tag not in f.get("tags", [])]
        return files

    def _apply_where(self, files: list[dict], clause: str) -> list[dict]:
        result = []
        for f in files:
            try:
                if self._evaluate_clause(f, clause):
                    result.append(f)
            except Exception:
                pass
        return result

    def _evaluate_clause(self, file_data: dict, clause: str) -> bool:
        clause = clause.strip()

        if " contains " in clause:
            field, _, value = clause.partition(" contains ")
            field = field.strip()
            value = value.strip().strip('"').strip("'")
            field_val = file_data.get(field, "")
            if isinstance(field_val, list):
                return value in field_val
            return value in str(field_val)

        if " = " in clause:
            field, _, value = clause.partition(" = ")
            field = field.strip()
            value = value.strip().strip('"').strip("'")
            return str(file_data.get(field, "")) == value

        if " != " in clause:
            field, _, value = clause.partition(" != ")
            field = field.strip()
            value = value.strip().strip('"').strip("'")
            return str(file_data.get(field, "")) != value

        if " > " in clause:
            field, _, value = clause.partition(" > ")
            return float(str(file_data.get(field.strip(), 0))) > float(value.strip())

        if " < " in clause:
            field, _, value = clause.partition(" < ")
            return float(str(file_data.get(field.strip(), 0))) < float(value.strip())

        if " and " in clause.lower():
            parts = re.split(r'\s+and\s+', clause, flags=re.IGNORECASE)
            return all(self._evaluate_clause(file_data, p) for p in parts)

        if " or " in clause.lower():
            parts = re.split(r'\s+or\s+', clause, flags=re.IGNORECASE)
            return any(self._evaluate_clause(file_data, p) for p in parts)

        return True

    def _apply_sort(self, files: list[dict], field: str, desc: bool) -> list[dict]:
        def sort_key(f):
            val = f.get(field, "")
            if isinstance(val, (int, float)):
                return val
            try:
                return float(val)
            except (ValueError, TypeError):
                return str(val)
        return sorted(files, key=sort_key, reverse=desc)

    def _apply_group(self, files: list[dict], field: str) -> list[dict]:
        groups = {}
        for f in files:
            key = f.get(field, "unknown")
            if key not in groups:
                groups[key] = []
            groups[key].append(f)
        result = []
        for key, items in groups.items():
            group_file = {"_group_key": key, "_group_count": len(items), "_group_items": items}
            group_file.update(items[0])
            result.append(group_file)
        return result

    def format_output(self, results: list[dict], query_type: str, fields: list[str]) -> str:
        if query_type == "LIST":
            lines = []
            for f in results:
                if fields:
                    vals = [str(f.get(field, "")) for field in fields]
                    lines.append("  " + ", ".join(vals))
                else:
                    lines.append(f"  - {f.get('name', f.get('file', ''))}")
            return "\n".join(lines)

        elif query_type == "TABLE":
            if not fields:
                fields = ["name", "folder", "tags"]
            header = " | ".join(f.capitalize() for f in fields)
            separator = " | ".join("-" * len(f) for f in fields)
            rows = []
            for f in results:
                row = " | ".join(str(f.get(field, ""))[:40] for field in fields)
                rows.append(row)
            return "\n".join([header, separator] + rows)

        elif query_type == "TASK":
            lines = []
            for f in results:
                for task in f.get("tasks", []):
                    status = "x" if task["completed"] else " "
                    lines.append(f"- [{status}] {task['text']} ({f.get('name', '')})")
            return "\n".join(lines)

        return str(results)


class DataviewEngine:
    """
    Main Dataview-style query engine.
    Usage:
        engine = DataviewEngine(vault_path)
        results = engine.query("LIST FROM #projects WHERE status = 'active'")
    """

    def __init__(self, vault_path: str):
        self.index = VaultIndex(vault_path)
        self.evaluator = DQLEvaluator(self.index)
        self.query_history = []

    def query(self, dql: str) -> dict:
        parser = DQLParser(dql)
        parsed = parser.parse()
        results = self.evaluator.execute(parsed)
        output = self.evaluator.format_output(results, parsed["query_type"], parsed["fields"])

        self.query_history.append({
            "query": dql,
            "result_count": len(results),
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        })

        return {
            "parsed": parsed,
            "results": results,
            "output": output,
            "count": len(results),
        }

    def refresh(self) -> None:
        self.index.refresh()

    def get_stats(self) -> dict:
        return {
            "total_files": len(self.index.files),
            "total_queries": len(self.query_history),
            "recent_queries": self.query_history[-10:],
        }


_global_dataview: Optional[DataviewEngine] = None


def get_dataview_engine(vault_path: str = None) -> DataviewEngine:
    global _global_dataview
    if _global_dataview is None:
        if vault_path is None:
            vault_path = str(Path(os.environ.get("OMNIS_VAULT_PATH", r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain")))
        _global_dataview = DataviewEngine(vault_path)
    return _global_dataview
