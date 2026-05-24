"""
LAIS Worktree Manager - Git worktree isolation for parallel agents.
Based on GasTown/GasTown worktree patterns.
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re

WORKTREE_DIR = Path(__file__).resolve().parent.parent.parent / "worktrees"
WORKTREE_CONFIG = WORKTREE_DIR / "config.json"
WORKTREE_LOG = WORKTREE_DIR / "worktree_log.json"


@dataclass
class WorktreeInfo:
    name: str
    path: Path
    branch: str
    task_id: Optional[str] = None
    created_at: str = None
    status: str = "active"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class WorktreeManager:
    """
    Manages git worktrees for parallel agent execution.
    Each task gets isolated workspace - no context bleeding.
    """

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or self._detect_repo()
        self.worktrees: Dict[str, WorktreeInfo] = {}
        self._ensure_dirs()
        self._load_config()

    def _detect_repo(self) -> Path:
        """Detect git repo from current directory or LAIS root."""
        lais_root = Path(__file__).resolve().parent.parent.parent
        git_dir = lais_root / ".git"
        if git_dir.exists():
            return lais_root
        # Check parent for git repo
        for parent in [lais_root.parent, lais_root.parent.parent]:
            if (parent / ".git").exists():
                return parent
        return lais_root

    def _ensure_dirs(self):
        WORKTREE_DIR.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        if WORKTREE_CONFIG.exists():
            try:
                data = json.loads(WORKTREE_CONFIG.read_text())
                for name, info in data.get("worktrees", {}).items():
                    self.worktrees[name] = WorktreeInfo(
                        name=name,
                        path=Path(info["path"]),
                        branch=info["branch"],
                        task_id=info.get("task_id"),
                        created_at=info.get("created_at"),
                        status=info.get("status", "active")
                    )
            except Exception:
                pass

    def _save_config(self):
        data = {
            "repo_path": str(self.repo_path),
            "worktrees": {
                name: {
                    "path": str(info.path),
                    "branch": info.branch,
                    "task_id": info.task_id,
                    "created_at": info.created_at,
                    "status": info.status
                }
                for name, info in self.worktrees.items()
            }
        }
        WORKTREE_CONFIG.write_text(json.dumps(data, indent=2))

    def _run_git(self, args: List[str], cwd: Optional[Path] = None) -> tuple:
        """Run git command, return (success, output, error)."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return False, "", str(e)

    def create_worktree(self, name: str, branch: str = None, task_id: str = None) -> Dict[str, Any]:
        """
        Create isolated worktree for task/agent.

        Args:
            name: Worktree name (unique identifier)
            branch: Branch name (auto-generated if None)
            task_id: Optional task association

        Returns:
            Dict with status, path, branch info
        """
        if name in self.worktrees:
            return {
                "status": "exists",
                "path": str(self.worktrees[name].path),
                "branch": self.worktrees[name].branch
            }

        # Generate branch name if not provided
        if branch is None:
            branch = f"wt/{name.replace(' ', '-').lower()[:30]}"

        # Create worktree path
        wt_path = WORKTREE_DIR / name

        # Ensure parent exists
        wt_path.mkdir(parents=True, exist_ok=True)

        # Create git worktree
        success, output, error = self._run_git([
            "worktree", "add",
            "-b", branch,
            str(wt_path),
            "HEAD"
        ])

        if not success:
            # Try without new branch if it exists
            success, output, error = self._run_git([
                "worktree", "add",
                str(wt_path),
                "HEAD"
            ])

        if success:
            info = WorktreeInfo(
                name=name,
                path=wt_path,
                branch=branch,
                task_id=task_id
            )
            self.worktrees[name] = info
            self._save_config()
            self._log_event("created", name, f"Worktree created: {wt_path}")

            return {
                "status": "created",
                "path": str(wt_path),
                "branch": branch,
                "task_id": task_id
            }
        else:
            return {
                "status": "error",
                "error": error,
                "suggestion": "Ensure git repo has HEAD for worktree creation"
            }

    def list_worktrees(self) -> List[Dict]:
        """List all active worktrees."""
        return [
            {
                "name": info.name,
                "path": str(info.path),
                "branch": info.branch,
                "task_id": info.task_id,
                "status": info.status,
                "created_at": info.created_at
            }
            for info in self.worktrees.values()
        ]

    def get_worktree(self, name: str) -> Optional[Dict]:
        """Get worktree info by name."""
        if name not in self.worktrees:
            return None
        info = self.worktrees[name]
        return {
            "name": info.name,
            "path": str(info.path),
            "branch": info.branch,
            "task_id": info.task_id,
            "status": info.status
        }

    def remove_worktree(self, name: str, force: bool = False) -> Dict:
        """Remove worktree and optionally delete branch."""
        if name not in self.worktrees:
            return {"status": "error", "message": f"Worktree '{name}' not found"}

        info = self.worktrees[name]
        branch = info.branch

        # Remove git worktree
        success, output, error = self._run_git(["worktree", "remove", name, "--force" if force else ""])

        if success:
            # Delete branch
            self._run_git(["branch", "-d", branch])
            del self.worktrees[name]
            self._save_config()
            self._log_event("removed", name, f"Worktree removed: {info.path}")

            return {
                "status": "removed",
                "name": name,
                "branch": branch
            }
        else:
            return {
                "status": "error",
                "error": error
            }

    def prune_worktrees(self) -> Dict:
        """Clean up stale worktree references."""
        success, output, error = self._run_git(["worktree", "prune"])
        return {
            "status": "pruned" if success else "error",
            "output": output,
            "error": error
        }

    def isolate_for_task(self, task_id: str) -> Dict:
        """Create isolated worktree for a specific task."""
        name = f"task_{task_id}"
        return self.create_worktree(name, task_id=task_id)

    def cleanup_old_worktrees(self, hours: int = 24) -> Dict:
        """Remove worktrees older than specified hours."""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=hours)
        removed = []

        for name, info in list(self.worktrees.items()):
            created = datetime.fromisoformat(info.created_at)
            if created < cutoff and info.status != "locked":
                result = self.remove_worktree(name)
                if result["status"] == "removed":
                    removed.append(name)

        return {
            "removed": removed,
            "count": len(removed),
            "remaining": len(self.worktrees)
        }

    def _log_event(self, event: str, worktree_name: str, detail: str):
        """Log worktree events."""
        log_file = WORKTREE_DIR / "events.json"
        try:
            events = json.loads(log_file.read_text()) if log_file.exists() else []
        except Exception:
            events = []
        events.append({
            "event": event,
            "worktree": worktree_name,
            "detail": detail,
            "timestamp": datetime.now().isoformat()
        })
        events = events[-500:]
        log_file.write_text(json.dumps(events, indent=2))


def load_worktree_manager(repo_path: Optional[Path] = None) -> WorktreeManager:
    return WorktreeManager(repo_path)


if __name__ == "__main__":
    print("=== LAIS Worktree Manager ===\n")
    manager = load_worktree_manager()

    print(f"Repo: {manager.repo_path}")
    print(f"Worktrees: {len(manager.worktrees)}")

    # Demo: create test worktree
    result = manager.create_worktree("test-agent", task_id="demo")
    print(f"\nCreate test: {result}")

    # List
    print("\nActive worktrees:")
    for wt in manager.list_worktrees():
        print(f"  - {wt['name']}: {wt['path']}")

    print("\nWorktree manager ready.")