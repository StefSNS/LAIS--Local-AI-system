"""LAIS Vault MCP Server - Obsidian vault search and sync tools."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP


VAULT_PATH = Path(os.environ.get("LAIS_VAULT_PATH",
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "vault"))
INDEX_PATH = Path(os.path.dirname(__file__)).parent / "vault_index_cache.json"


mcp = FastMCP("LAIS Vault", json_response=True)


def _load_index() -> dict[str, Any]:
    if INDEX_PATH.exists():
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_index(index: dict[str, Any]) -> None:
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


def _build_index() -> dict[str, Any]:
    index = {"notes": {}, "last_updated": datetime.now().isoformat()}
    if not VAULT_PATH.exists():
        return index

    for md_file in VAULT_PATH.rglob("*.md"):
        rel_path = str(md_file.relative_to(VAULT_PATH))
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        lines = content.split("\n")
        frontmatter_end = 0
        in_frontmatter = False
        for i, line in enumerate(lines):
            if line.strip() == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    frontmatter_end = i
                continue

        body = "\n".join(lines[frontmatter_end + 1:])

        index["notes"][rel_path] = {
            "path": rel_path,
            "title": md_file.stem,
            "folder": str(md_file.parent.relative_to(VAULT_PATH)),
            "word_count": len(body.split()),
            "content_preview": body[:500],
            "last_modified": datetime.fromtimestamp(md_file.stat().st_mtime).isoformat(),
        }
    return index


@mcp.tool()
def search_vault(query: str, max_results: int = 10) -> str:
    """Search Obsidian vault by query string across all notes."""
    index = _load_index()
    if not index.get("notes"):
        index = _build_index()
        _save_index(index)

    results = []
    query_lower = query.lower()
    for note_path, note_data in index["notes"].items():
        preview = note_data.get("content_preview", "")
        if query_lower in preview.lower() or query_lower in note_path.lower():
            results.append({
                "path": note_path,
                "title": note_data.get("title", ""),
                "folder": note_data.get("folder", ""),
                "preview": preview[:300],
            })

    results = sorted(results, key=lambda x: x["path"])[:max_results]
    if not results:
        return "No results found."
    return json.dumps(results, indent=2)


@mcp.tool()
def read_vault_note(path: str) -> str:
    """Read the full content of a vault note by path."""
    if ".." in path or path.startswith("/"):
        return "Invalid path."

    file_path = VAULT_PATH / path
    if not file_path.exists():
        return f"File not found: {path}"

    try:
        content = file_path.read_text(encoding="utf-8")
        return content
    except Exception as e:
        return f"Error reading file: {e}"


@mcp.tool()
def list_vault_notes(folder: str = "") -> str:
    """List all notes in vault, optionally filtered by folder."""
    index = _load_index()
    if not index.get("notes"):
        index = _build_index()
        _save_index(index)

    notes = []
    for note_path, note_data in index["notes"].items():
        note_folder = note_data.get("folder", "")
        if folder and folder not in note_folder:
            continue
        notes.append({
            "path": note_path,
            "title": note_data.get("title", ""),
            "folder": note_folder,
            "word_count": note_data.get("word_count", 0),
        })

    notes = sorted(notes, key=lambda x: x["path"])
    return json.dumps(notes, indent=2)


@mcp.tool()
def write_vault_note(path: str, content: str) -> str:
    """Write or update a vault note."""
    if ".." in path or path.startswith("/"):
        return "Invalid path."

    file_path = VAULT_PATH / path
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        file_path.write_text(content, encoding="utf-8")
        return f"Note written: {path}"
    except Exception as e:
        return f"Error writing file: {e}"


@mcp.tool()
def refresh_vault_index() -> str:
    """Force rebuild the vault search index."""
    index = _build_index()
    _save_index(index)
    note_count = len(index.get("notes", {}))
    return f"Vault index rebuilt. Indexed {note_count} notes."


@mcp.resource("vault://index")
def get_vault_index() -> str:
    """Return the full vault search index."""
    index = _load_index()
    if not index.get("notes"):
        index = _build_index()
        _save_index(index)
    return json.dumps(index, indent=2, default=str)


if __name__ == "__main__":
    mcp.run(transport="stdio")