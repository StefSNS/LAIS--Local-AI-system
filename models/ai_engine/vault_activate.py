"""
Vault Sync Activator - Bridges LAIS memory to Obsidian vault

Usage:
    python vault_activate.py                    # One-shot sync
    python vault_activate.py --watch            # Watch mode (polls every 60s)
    python vault_activate.py --status           # Check sync status
"""

import json
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

VAULT = Path(__file__).resolve().parent.parent.parent.parent / "vault"
LAIS_CRYSTAL = Path(__file__).parent / "knowledge" / "memory" / "crystallized.json"
VAULT_CRYSTAL = VAULT / "50_Memory" / "crystallized.json"
VAULT_LOG = VAULT / "50_Memory" / "Decision Log.md"
SYNC_LOG = Path(__file__).parent / "knowledge" / "memory" / "sync_log.json"


def load_json(path: Path) -> list:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data.get("learnings", [])
            if isinstance(data, list):
                return data
            return []
        except:
            return []
    return []


def save_json(path: Path, data: list, keep_dict: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if keep_dict:
        out = {"learnings": data, "decision_log": [], "last_crystallized": datetime.now(timezone.utc).isoformat()}
    else:
        out = data
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")


def merge_entries(lais_entries: list, vault_entries: list, source: str = "opencode") -> int:
    """Merge LAIS entries into vault, deduplicating by key hash."""
    vault_keys = {e["key"] for e in vault_entries}
    new_count = 0

    for entry in lais_entries:
        key = entry.get("key", "")
        if key and key not in vault_keys:
            entry["source"] = source
            entry["created"] = entry.get("created") or datetime.now(timezone.utc).isoformat()
            entry["updated"] = datetime.now(timezone.utc).isoformat()
            vault_entries.append(entry)
            vault_keys.add(key)
            new_count += 1

    return new_count


def crystallize(key: str, value: str, sources: list = None, priority: str = "medium"):
    """Crystallize a learning to both LAIS and Obsidian vault."""
    entry = {
        "key": key,
        "value": value,
        "created": datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(),
        "sources": sources or ["opencode"],
        "priority": priority
    }

    # Write to LAIS (dict format with learnings key)
    lais_data = load_json(LAIS_CRYSTAL)
    lais_data.append(entry)
    save_json(LAIS_CRYSTAL, lais_data, keep_dict=True)

    # Write to Obsidian vault (list format)
    vault_data = load_json(VAULT_CRYSTAL)
    vault_data.append(entry)
    save_json(VAULT_CRYSTAL, vault_data)

    # Also write a markdown file
    safe_key = "".join(c if c.isalnum() or c in " _-" else "_" for c in key)[:50]
    md_path = VAULT / "50_Memory" / "learnings" / f"{safe_key}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(
        f"---\nkey: {key}\ncreated: {entry['created']}\npriority: {priority}\n---\n\n# {key}\n\n{value}\n",
        encoding="utf-8"
    )

    print(f"\n  crystallized: {key[:60]}")

    # Log sync
    log = load_json(SYNC_LOG)
    log.append({
        "action": "crystallize",
        "key": key,
        "timestamp": entry["created"]
    })
    save_json(SYNC_LOG, log[-100:])

    return entry


def sync_all():
    """Full sync: merge LAIS→vault, then vault→LAIS."""
    lais_entries = load_json(LAIS_CRYSTAL)
    vault_entries = load_json(VAULT_CRYSTAL)

    lais_to_vault = merge_entries(lais_entries, vault_entries, "opencode")
    vault_to_lais = merge_entries(vault_entries, lais_entries, "vault")

    if lais_to_vault:
        save_json(VAULT_CRYSTAL, vault_entries)
    if vault_to_lais:
        save_json(LAIS_CRYSTAL, lais_entries, keep_dict=True)

    log = load_json(SYNC_LOG)
    log.append({
        "action": "sync_all",
        "lais_to_vault": lais_to_vault,
        "vault_to_lais": vault_to_lais,
        "total_vault": len(vault_entries),
        "total_lais": len(lais_entries),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    save_json(SYNC_LOG, log[-100:])

    return lais_to_vault, vault_to_lais


def show_status():
    lais = load_json(LAIS_CRYSTAL)
    vault = load_json(VAULT_CRYSTAL)
    log = load_json(SYNC_LOG)
    last_sync = log[-1]["timestamp"] if log else "never"

    print("\n=== Vault Sync Status ===")
    print(f"  LAIS crystallized:   {len(lais)} entries")
    print(f"  Obsidian vault:      {len(vault)} entries")
    print(f"  Last sync:           {last_sync}")
    print(f"  Sync log entries:    {len(log)}")
    print(f"  Vault path:          {VAULT}")
    print(f"  LAIS crystal:        {LAIS_CRYSTAL}")


def watch_loop(interval: int = 60):
    print(f"\nWatching for changes every {interval}s (Ctrl+C to stop)")
    while True:
        l2v, v2l = sync_all()
        if l2v or v2l:
            print(f"  synced: {l2v}→vault, {v2l}→LAIS @ {datetime.now().isoformat()[:19]}")
        time.sleep(interval)


if __name__ == "__main__":
    if "--status" in sys.argv:
        show_status()
    elif "--watch" in sys.argv:
        show_status()
        watch_loop()
    else:
        show_status()
        l2v, v2l = sync_all()
        print(f"\n  Synced: {l2v} LAIS -> vault, {v2l} vault -> LAIS")
        print("  Ready. Run with --watch for continuous sync or --status to check.")
