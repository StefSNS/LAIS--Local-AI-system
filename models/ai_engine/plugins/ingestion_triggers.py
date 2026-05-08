"""
Automated Document Ingestion Triggers - Monitors knowledge vault for new/updated
documents and automatically triggers semantic index rebuilds.

Features:
- File system watcher for new .md/.txt files
- Scheduled rebuilds at configurable intervals
- Manual trigger API
- Change detection to avoid unnecessary rebuilds
"""

import os
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime

VAULT_PATH = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge")
INDEX_PATH = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\txtai_index")
STATE_FILE = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\ingestion_state.json")


class IngestionTrigger:
    """Monitors knowledge vault and triggers index rebuilds when needed."""

    def __init__(self, vault_path: Optional[Path] = None):
        self.vault_path = vault_path or VAULT_PATH
        self.state_file = STATE_FILE
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._file_hashes: Dict[str, str] = {}
        self._callbacks: List[Callable] = []
        self._last_rebuild: Optional[datetime] = None
        self._load_state()

    def _load_state(self):
        """Load previous file hash state."""
        import json
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                self._file_hashes = state.get("file_hashes", {})
                self._last_rebuild = datetime.fromisoformat(state["last_rebuild"]) if state.get("last_rebuild") else None
            except Exception:
                self._file_hashes = {}

    def _save_state(self):
        """Persist current file hash state."""
        import json
        state = {
            "file_hashes": self._file_hashes,
            "last_rebuild": self._last_rebuild.isoformat() if self._last_rebuild else None,
            "total_files": len(self._file_hashes),
        }
        self.state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def _hash_file(self, fpath: Path) -> str:
        """Compute MD5 hash of file content."""
        try:
            content = fpath.read_bytes()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return ""

    def _scan_vault(self) -> Dict[str, str]:
        """Scan vault and compute hashes for all indexable files."""
        hashes = {}
        supported = (".md", ".txt", ".json")

        for root, _, files in os.walk(self.vault_path):
            if "node_modules" in root or ".git" in root:
                continue
            for fname in files:
                if not fname.lower().endswith(supported):
                    continue
                fpath = Path(root) / fname
                rel_path = str(fpath.relative_to(self.vault_path))
                hashes[rel_path] = self._hash_file(fpath)

        return hashes

    def detect_changes(self) -> Dict[str, List[str]]:
        """Detect new, modified, and deleted files since last scan."""
        current_hashes = self._scan_vault()
        old_hashes = self._file_hashes

        new_files = [f for f in current_hashes if f not in old_hashes]
        modified_files = [f for f in current_hashes if f in old_hashes and current_hashes[f] != old_hashes[f]]
        deleted_files = [f for f in old_hashes if f not in current_hashes]

        return {
            "new": new_files,
            "modified": modified_files,
            "deleted": deleted_files,
        }

    def has_changes(self) -> bool:
        """Quick check if any changes detected."""
        changes = self.detect_changes()
        return bool(changes["new"] or changes["modified"] or changes["deleted"])

    def trigger_rebuild(self, force: bool = False) -> Dict:
        """Trigger index rebuild if changes detected or forced."""
        changes = self.detect_changes()
        has_any = bool(changes["new"] or changes["modified"] or changes["deleted"])

        if not force and not has_any:
            return {
                "rebuilt": False,
                "reason": "no changes detected",
                "timestamp": datetime.now().isoformat(),
            }

        # Update state before rebuild
        self._file_hashes = self._scan_vault()
        self._save_state()

        # Rebuild index
        result = {
            "rebuilt": True,
            "changes": changes,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Handle both direct execution and module import
            import sys
            plugin_dir = Path(__file__).resolve().parent.parent
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir))
            from plugins.semantic_search import load_txtai_search
            search = load_txtai_search()
            search.rebuild()
            stats = search.get_stats()
            result["documents_indexed"] = stats.get("documents", 0)
            result["success"] = True
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        self._last_rebuild = datetime.now()
        self._save_state()

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(result)
            except Exception:
                pass

        return result

    def on_rebuild(self, callback: Callable):
        """Register a callback for rebuild events."""
        self._callbacks.append(callback)

    def watch_loop(self, interval: int = 300, auto_rebuild: bool = True):
        """
        Run a continuous watch loop.
        interval: seconds between scans
        auto_rebuild: whether to automatically rebuild on changes
        """
        print(f"[IngestionTrigger] Watching vault: {self.vault_path}")
        print(f"[IngestionTrigger] Scan interval: {interval}s, Auto-rebuild: {auto_rebuild}")

        while True:
            try:
                changes = self.detect_changes()
                has_any = bool(changes["new"] or changes["modified"] or changes["deleted"])

                if has_any:
                    print(f"[IngestionTrigger] Changes detected:")
                    if changes["new"]:
                        print(f"  New: {len(changes['new'])} files")
                    if changes["modified"]:
                        print(f"  Modified: {len(changes['modified'])} files")
                    if changes["deleted"]:
                        print(f"  Deleted: {len(changes['deleted'])} files")

                    if auto_rebuild:
                        result = self.trigger_rebuild()
                        print(f"[IngestionTrigger] Rebuild: {result.get('success', False)}, "
                              f"docs: {result.get('documents_indexed', 0)}")
                else:
                    print(f"[IngestionTrigger] No changes detected")

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n[IngestionTrigger] Watch loop stopped")
                break
            except Exception as e:
                print(f"[IngestionTrigger] Error: {e}")
                time.sleep(interval)

    def get_status(self) -> Dict:
        """Get current trigger status."""
        changes = self.detect_changes()
        return {
            "total_files": len(self._file_hashes),
            "last_rebuild": self._last_rebuild.isoformat() if self._last_rebuild else None,
            "pending_changes": {
                "new": len(changes["new"]),
                "modified": len(changes["modified"]),
                "deleted": len(changes["deleted"]),
            },
            "callbacks_registered": len(self._callbacks),
        }


def load_trigger(vault_path=None) -> IngestionTrigger:
    """Factory function."""
    return IngestionTrigger(vault_path)


if __name__ == "__main__":
    print("=== Automated Ingestion Triggers ===")
    trigger = load_trigger()

    status = trigger.get_status()
    print(f"Status: {status}")

    print("\n=== Change Detection ===")
    changes = trigger.detect_changes()
    print(f"New files: {len(changes['new'])}")
    print(f"Modified files: {len(changes['modified'])}")
    print(f"Deleted files: {len(changes['deleted'])}")

    if changes['new'][:3]:
        print(f"  New: {changes['new'][:3]}")
    if changes['modified'][:3]:
        print(f"  Modified: {changes['modified'][:3]}")

    print("\n=== Manual Rebuild Trigger ===")
    result = trigger.trigger_rebuild(force=True)
    print(f"Result: {result}")
