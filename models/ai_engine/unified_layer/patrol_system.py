"""
LAIS Patrol System — Self-healing agent coordination.
Based on OpenMOSS patrol concept with recovery and escalation.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

PATROL_LOG = Path(__file__).resolve().parent.parent / "knowledge" / "memory" / "patrol_log.json"
PATROL_CONFIG = Path(__file__).resolve().parent.parent / "knowledge" / "memory" / "patrol_config.json"


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    DEAD = "dead"


@dataclass
class TaskState:
    task_id: str
    status: str = "pending"
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    recovery_actions: List[str] = field(default_factory=list)
    health: HealthStatus = HealthStatus.HEALTHY


class PatrolSystem:
    """
    Self-healing patrol system for LAIS agents.
    Monitors task health, triggers recovery, escalates failures.
    """

    def __init__(self):
        self.tasks: Dict[str, TaskState] = {}
        self.config = self._load_config()
        self._load_tasks()
        self.patrol_interval = self.config.get("patrol_interval", 60)
        self.max_recovery_attempts = self.config.get("max_recovery_attempts", 3)
        self.escalation_threshold = self.config.get("escalation_threshold", 2)

    def _load_config(self) -> Dict:
        if PATROL_CONFIG.exists():
            return json.loads(PATROL_CONFIG.read_text())
        return {
            "patrol_interval": 60,
            "max_recovery_attempts": 3,
            "escalation_threshold": 2,
            "recovery_strategies": {
                "retry": "Re-execute with same context",
                "replan": "Re-plan the task with fresh approach",
                "escalate": "Escalate to human review"
            }
        }

    def _save_config(self):
        PATROL_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        PATROL_CONFIG.write_text(json.dumps(self.config, indent=2))

    def _load_tasks(self):
        if PATROL_LOG.exists():
            try:
                data = json.loads(PATROL_LOG.read_text())
                for task_data in data.get("tasks", []):
                    task_data["health"] = HealthStatus(task_data.get("health", "healthy"))
                    self.tasks[task_data["task_id"]] = TaskState(**task_data)
            except Exception:
                pass

    def _save_tasks(self):
        PATROL_LOG.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "last_patrol": datetime.now().isoformat(),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "status": t.status,
                    "attempts": t.attempts,
                    "max_attempts": t.max_attempts,
                    "last_error": t.last_error,
                    "created_at": t.created_at,
                    "last_updated": t.last_updated,
                    "recovery_actions": t.recovery_actions,
                    "health": t.health.value
                }
                for t in self.tasks.values()
            ]
        }
        PATROL_LOG.write_text(json.dumps(data, indent=2))

    def register_task(self, task_id: str, max_attempts: int = 3) -> TaskState:
        task = TaskState(task_id=task_id, max_attempts=max_attempts)
        self.tasks[task_id] = task
        self._log_patrol_event("task_registered", task_id, f"Task registered with {max_attempts} max attempts")
        self._save_tasks()
        return task

    def mark_attempt(self, task_id: str, error: Optional[str] = None) -> Dict[str, Any]:
        task = self.tasks.get(task_id)
        if not task:
            return {"status": "error", "message": f"Task {task_id} not found"}

        task.attempts += 1
        task.last_updated = datetime.now().isoformat()
        task.last_error = error

        if error:
            self._log_patrol_event("attempt_failed", task_id, error)

        recovery_action = self._determine_recovery_action(task)
        if recovery_action:
            task.recovery_actions.append({
                "action": recovery_action,
                "timestamp": datetime.now().isoformat(),
                "attempt": task.attempts
            })

        self._update_health(task)
        self._save_tasks()

        return {
            "status": "in_progress",
            "task_id": task_id,
            "attempt": task.attempts,
            "recovery_action": recovery_action,
            "health": task.health.value
        }

    def mark_success(self, task_id: str) -> Dict[str, Any]:
        task = self.tasks.get(task_id)
        if not task:
            return {"status": "error", "message": f"Task {task_id} not found"}

        task.status = "completed"
        task.health = HealthStatus.HEALTHY
        task.last_updated = datetime.now().isoformat()
        self._log_patrol_event("task_completed", task_id, "Task completed successfully")
        self._save_tasks()

        return {
            "status": "completed",
            "task_id": task_id,
            "attempts": task.attempts,
            "health": task.health.value
        }

    def _determine_recovery_action(self, task: TaskState) -> Optional[str]:
        if task.attempts < task.max_attempts:
            if task.attempts == 1:
                return "retry"
            elif task.attempts == 2:
                return "replan"
            else:
                return "escalate"
        else:
            task.health = HealthStatus.DEAD
            return "dead"

    def _update_health(self, task: TaskState):
        if task.attempts == 0:
            task.health = HealthStatus.HEALTHY
        elif task.attempts == 1:
            task.health = HealthStatus.DEGRADED
        elif task.attempts >= 2:
            task.health = HealthStatus.FAILING

        if task.attempts >= task.max_attempts:
            task.health = HealthStatus.DEAD
            self._log_patrol_event("task_dead", task.task_id, f"Task exceeded max attempts: {task.max_attempts}")

    def get_task_health(self, task_id: str) -> Optional[Dict]:
        task = self.tasks.get(task_id)
        if not task:
            return None
        return {
            "task_id": task.task_id,
            "health": task.health.value,
            "attempts": task.attempts,
            "max_attempts": task.max_attempts,
            "last_error": task.last_error,
            "recovery_actions": task.recovery_actions,
            "status": task.status
        }

    def get_all_health(self) -> Dict[str, List[Dict]]:
        by_health = {h.value: [] for h in HealthStatus}
        for task in self.tasks.values():
            by_health[task.health.value].append({
                "task_id": task.task_id,
                "attempts": task.attempts,
                "status": task.status
            })
        return by_health

    def _log_patrol_event(self, event: str, task_id: str, detail: str):
        log_file = Path(__file__).resolve().parent.parent / "knowledge" / "memory" / "patrol_events.json"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            events = json.loads(log_file.read_text()) if log_file.exists() else []
        except Exception:
            events = []
        events.append({
            "event": event,
            "task_id": task_id,
            "detail": detail,
            "timestamp": datetime.now().isoformat()
        })
        events = events[-500:]
        log_file.write_text(json.dumps(events, indent=2))

    def cleanup_old_tasks(self, hours: int = 24):
        cutoff = datetime.now() - timedelta(hours=hours)
        to_remove = []
        for task_id, task in self.tasks.items():
            last_updated = datetime.fromisoformat(task.last_updated)
            if last_updated < cutoff and task.status == "completed":
                to_remove.append(task_id)
        for task_id in to_remove:
            del self.tasks[task_id]
        self._save_tasks()
        return {"removed": len(to_remove), "remaining": len(self.tasks)}


def load_patrol_system() -> PatrolSystem:
    return PatrolSystem()


if __name__ == "__main__":
    patrol = load_patrol_system()
    print("=== LAIS Patrol System ===\n")
    print(f"Registered tasks: {len(patrol.tasks)}")
    print(f"Patrol interval: {patrol.patrol_interval}s\n")

    task_id = "test_task_1"
    patrol.register_task(task_id, max_attempts=3)
    print(f"Registered task: {task_id}")

    result = patrol.mark_attempt(task_id, "Initial failure")
    print(f"Attempt 1: {result}")

    result = patrol.mark_attempt(task_id, "Second failure")
    print(f"Attempt 2: {result}")

    health = patrol.get_task_health(task_id)
    print(f"\nTask health: {health}")

    all_health = patrol.get_all_health()
    print(f"\nAll health status: {all_health}")

    print("\nPatrol system ready.")