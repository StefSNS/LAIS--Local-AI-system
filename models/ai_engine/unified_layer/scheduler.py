"""
Scheduler - Phase 3 of Architecture Evolution
Cron-style automation for recurring tasks, natural language scheduling,
persistent task persistence across restarts, and Oz-style cloud agent dispatch.
"""

import json
import re
import time
import uuid
import threading
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from threading import Lock

TASKS_FILE = Path(
    Path(__file__).resolve().parent.parent / "knowledge" / "memory" / "scheduled_tasks.json"
)
CLOUD_TASKS_FILE = Path(
    Path(__file__).resolve().parent.parent / "knowledge" / "memory" / "cloud_tasks.json"
)
TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
LOCK = Lock()


class ScheduledTask:
    """Represents a scheduled recurring task."""

    def __init__(
        self,
        task_id: str,
        name: str,
        action_type: str,
        details: Dict[str, Any],
        schedule: str,
        agent: str = "auto",
        enabled: bool = True,
        created_by: str = "user",
    ):
        self.task_id = task_id
        self.name = name
        self.action_type = action_type
        self.details = details
        self.schedule = schedule
        self.agent = agent
        self.enabled = enabled
        self.created_by = created_by
        self.created_at = datetime.now().isoformat()
        self.last_run = None
        self.last_result = None
        self.run_count = 0
        self.next_run = self._calc_next_run()

    def _calc_next_run(self) -> Optional[str]:
        """Calculate next run time from schedule expression."""
        now = datetime.now()

        # Parse schedule expression
        parts = self.schedule.strip().lower().split()

        if not parts:
            return None

        try:
            if parts[0] == "every":
                return self._parse_every(parts[1:], now)
            elif parts[0] == "at":
                return self._parse_at(parts[1:], now)
            elif parts[0] == "daily":
                return self._parse_daily(parts[1:], now)
            elif parts[0] == "weekly":
                return self._parse_weekly(parts[1:], now)
            elif parts[0] == "monthly":
                return self._parse_monthly(parts[1:], now)
            elif parts[0] == "once":
                return self._parse_once(parts[1:], now)
            else:
                return self._parse_cron(parts, now)
        except Exception as e:
            return None

    def _parse_every(self, parts: List[str], now: datetime) -> Optional[str]:
        """Parse 'every N minutes/hours/days'."""
        if not parts:
            return None

        try:
            n = int(parts[0])
        except ValueError:
            return None

        unit = parts[1] if len(parts) > 1 else "hours"

        if "min" in unit:
            delta = timedelta(minutes=n)
        elif "hour" in unit:
            delta = timedelta(hours=n)
        elif "day" in unit:
            delta = timedelta(days=n)
        elif "week" in unit:
            delta = timedelta(weeks=n)
        else:
            return None

        next_time = now + delta
        return next_time.isoformat()

    def _parse_at(self, parts: List[str], now: datetime) -> Optional[str]:
        """Parse 'at HH:MM' (today or tomorrow)."""
        if not parts:
            return None

        time_str = parts[0]
        match = re.match(r"(\d{1,2}):(\d{2})", time_str)
        if not match:
            return None

        hour, minute = int(match.group(1)), int(match.group(2))
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if target <= now:
            target += timedelta(days=1)

        return target.isoformat()

    def _parse_daily(self, parts: List[str], now: datetime) -> Optional[str]:
        """Parse 'daily at HH:MM'."""
        if not parts or parts[0] != "at":
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

        time_str = parts[1]
        match = re.match(r"(\d{1,2}):(\d{2})", time_str)
        if not match:
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

        hour, minute = int(match.group(1)), int(match.group(2))
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if target <= now:
            target += timedelta(days=1)

        return target.isoformat()

    def _parse_weekly(self, parts: List[str], now: datetime) -> Optional[str]:
        """Parse 'weekly on [day] at HH:MM'."""
        days = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6,
            "mon": 0, "tue": 1, "wed": 2, "thu": 3,
            "fri": 4, "sat": 5, "sun": 6,
        }

        if not parts or parts[0] != "on":
            return now + timedelta(weeks=1)

        day_name = parts[1] if len(parts) > 1 else now.strftime("%A").lower()
        target_weekday = days.get(day_name, now.weekday())

        days_ahead = target_weekday - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7

        target = now + timedelta(days=days_ahead)

        if len(parts) > 3 and parts[2] == "at":
            time_match = re.match(r"(\d{1,2}):(\d{2})", parts[3])
            if time_match:
                hour, minute = int(time_match.group(1)), int(time_match.group(2))
                target = target.replace(hour=hour, minute=minute, second=0, microsecond=0)

        return target.isoformat()

    def _parse_monthly(self, parts: List[str], now: datetime) -> Optional[str]:
        """Parse 'monthly on day N at HH:MM'."""
        day = 1
        hour, minute = 0, 0

        if parts and parts[0] == "on":
            if len(parts) > 1:
                try:
                    day = int(parts[1])
                except ValueError:
                    pass

            if len(parts) > 3 and parts[2] == "at":
                time_match = re.match(r"(\d{1,2}):(\d{2})", parts[3])
                if time_match:
                    hour, minute = int(time_match.group(1)), int(time_match.group(2))

        target = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)

        if target <= now:
            if target.month == 12:
                target = target.replace(year=target.year + 1, month=1, day=day)
            else:
                target = target.replace(month=target.month + 1, day=day)

        return target.isoformat()

    def _parse_once(self, parts: List[str], now: datetime) -> Optional[str]:
        """Parse 'once in N minutes/hours'."""
        return self._parse_every(parts, now)

    def _parse_cron(self, parts: List[str], now: datetime) -> Optional[str]:
        """Basic cron expression parsing (minute hour day month weekday)."""
        if len(parts) < 2:
            return None

        try:
            minute = int(parts[0]) if parts[0] != "*" else 0
            hour = int(parts[1]) if parts[1] != "*" else now.hour + 1
        except ValueError:
            return None

        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if target <= now:
            target += timedelta(days=1)

        return target.isoformat()

    def should_run(self) -> bool:
        """Check if this task should run now."""
        if not self.enabled or not self.next_run:
            return False

        next_time = datetime.fromisoformat(self.next_run)
        return datetime.now() >= next_time

    def record_run(self, success: bool, result: str = ""):
        """Record a task execution."""
        self.last_run = datetime.now().isoformat()
        self.last_result = result if success else f"FAILED: {result}"
        self.run_count += 1
        self.next_run = self._calc_next_run()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "action_type": self.action_type,
            "details": self.details,
            "schedule": self.schedule,
            "agent": self.agent,
            "enabled": self.enabled,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "last_run": self.last_run,
            "last_result": self.last_result,
            "run_count": self.run_count,
            "next_run": self.next_run,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledTask":
        task = cls(
            task_id=data["task_id"],
            name=data["name"],
            action_type=data["action_type"],
            details=data.get("details", {}),
            schedule=data["schedule"],
            agent=data.get("agent", "auto"),
            enabled=data.get("enabled", True),
            created_by=data.get("created_by", "user"),
        )
        task.created_at = data.get("created_at", datetime.now().isoformat())
        task.last_run = data.get("last_run")
        task.last_result = data.get("last_result")
        task.run_count = data.get("run_count", 0)
        task.next_run = data.get("next_run")
        return task


class CloudAgentTask:
    """Represents a task dispatched to a cloud agent (Oz-style)."""

    def __init__(
        self,
        task_id: str,
        name: str,
        prompt: str,
        agent_type: str = "general",
        webhook_url: str = "",
        schedule: str = "once in 0 minutes",
        priority: str = "normal",
        timeout_min: int = 30,
        metadata: Dict[str, Any] = None,
    ):
        self.task_id = task_id
        self.name = name
        self.prompt = prompt
        self.agent_type = agent_type
        self.webhook_url = webhook_url
        self.schedule = schedule
        self.priority = priority
        self.timeout_min = timeout_min
        self.metadata = metadata or {}
        self.status = "pending"
        self.created_at = datetime.now().isoformat()
        self.dispatched_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.retry_count = 0
        self.max_retries = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "prompt": self.prompt,
            "agent_type": self.agent_type,
            "webhook_url": self.webhook_url,
            "schedule": self.schedule,
            "priority": self.priority,
            "timeout_min": self.timeout_min,
            "metadata": self.metadata,
            "status": self.status,
            "created_at": self.created_at,
            "dispatched_at": self.dispatched_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CloudAgentTask":
        task = cls(
            task_id=data["task_id"],
            name=data["name"],
            prompt=data["prompt"],
            agent_type=data.get("agent_type", "general"),
            webhook_url=data.get("webhook_url", ""),
            schedule=data.get("schedule", "once in 0 minutes"),
            priority=data.get("priority", "normal"),
            timeout_min=data.get("timeout_min", 30),
            metadata=data.get("metadata", {}),
        )
        task.status = data.get("status", "pending")
        task.created_at = data.get("created_at", datetime.now().isoformat())
        task.dispatched_at = data.get("dispatched_at")
        task.completed_at = data.get("completed_at")
        task.result = data.get("result")
        task.error = data.get("error")
        task.retry_count = data.get("retry_count", 0)
        return task


class CloudAgentDispatcher:
    """
    Oz-style cloud agent dispatcher.
    Dispatches long-running tasks to cloud agents via webhooks.
    Supports: async dispatch, result callbacks, retry logic, task queue.
    """

    def __init__(self, default_webhook: str = ""):
        self.default_webhook = default_webhook
        self._tasks: Dict[str, CloudAgentTask] = {}
        self._result_handlers: Dict[str, Callable] = {}
        self._load()

    def dispatch(
        self,
        name: str,
        prompt: str,
        agent_type: str = "general",
        webhook_url: str = "",
        priority: str = "normal",
        timeout_min: int = 30,
        metadata: Dict[str, Any] = None,
    ) -> str:
        task_id = f"cloud_{uuid.uuid4().hex[:8]}"
        task = CloudAgentTask(
            task_id=task_id,
            name=name,
            prompt=prompt,
            agent_type=agent_type,
            webhook_url=webhook_url or self.default_webhook,
            priority=priority,
            timeout_min=timeout_min,
            metadata=metadata,
        )
        self._tasks[task_id] = task
        self._save()
        return task_id

    def dispatch_to_n8n(
        self,
        name: str,
        workflow_id: str,
        inputs: Dict[str, Any],
        webhook_url: str = "",
    ) -> str:
        prompt = json.dumps({"workflow": workflow_id, "inputs": inputs})
        return self.dispatch(
            name=name,
            prompt=prompt,
            agent_type="n8n_workflow",
            webhook_url=webhook_url,
            metadata={"workflow_id": workflow_id, "inputs": inputs},
        )

    def execute_task(self, task_id: str) -> Dict[str, Any]:
        task = self._tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}

        if not task.webhook_url:
            task.status = "failed"
            task.error = "No webhook URL configured"
            self._save()
            return {"error": "No webhook URL configured"}

        payload = {
            "task_id": task.task_id,
            "name": task.name,
            "prompt": task.prompt,
            "agent_type": task.agent_type,
            "priority": task.priority,
            "timeout_min": task.timeout_min,
            "metadata": task.metadata,
            "callback_url": f"http://localhost:8080/api/cloud-agent/callback/{task_id}",
        }

        try:
            task.status = "dispatched"
            task.dispatched_at = datetime.now().isoformat()
            self._save()

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                task.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                task.status = "completed"
                task.completed_at = datetime.now().isoformat()
                task.result = result
                self._save()
                return {"success": True, "result": result}

        except urllib.error.URLError as e:
            task.retry_count += 1
            if task.retry_count < task.max_retries:
                task.status = "retrying"
                task.error = f"Webhook error (attempt {task.retry_count}/{task.max_retries}): {e}"
            else:
                task.status = "failed"
                task.error = f"Webhook error after {task.max_retries} retries: {e}"
            self._save()
            return {"error": str(e), "retry_count": task.retry_count}
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            self._save()
            return {"error": str(e)}

    def register_result_handler(self, agent_type: str, handler: Callable):
        self._result_handlers[agent_type] = handler

    def handle_callback(self, task_id: str, result: Dict[str, Any]) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.status = "completed"
        task.completed_at = datetime.now().isoformat()
        task.result = result
        self._save()

        handler = self._result_handlers.get(task.agent_type)
        if handler:
            try:
                handler(task_id, result)
            except Exception:
                pass
        return True

    def get_task(self, task_id: str) -> Optional[CloudAgentTask]:
        return self._tasks.get(task_id)

    def list_tasks(self, status: str = None, limit: int = 50) -> List[Dict]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return [t.to_dict() for t in tasks[:limit]]

    def get_pending_tasks(self) -> List[Dict]:
        return self.list_tasks(status="pending")

    def cancel_task(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task and task.status in ("pending", "dispatched"):
            task.status = "cancelled"
            self._save()
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        by_status = {}
        for t in self._tasks.values():
            by_status[t.status] = by_status.get(t.status, 0) + 1
        return {
            "total_tasks": len(self._tasks),
            "by_status": by_status,
            "default_webhook": self.default_webhook,
        }

    def _load(self):
        if CLOUD_TASKS_FILE.exists():
            try:
                data = json.loads(CLOUD_TASKS_FILE.read_text(encoding="utf-8"))
                for t_data in data:
                    task = CloudAgentTask.from_dict(t_data)
                    if task.status not in ("completed", "failed", "cancelled"):
                        self._tasks[task.task_id] = task
            except Exception as e:
                pass
 
    def _save(self):
        try:
            CLOUD_TASKS_FILE.write_text(
                json.dumps([t.to_dict() for t in self._tasks.values()], indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            pass
 
 
class TaskScheduler:
    """
    Scheduler for recurring automated tasks.
    - Natural language scheduling
    - Cron-style expressions
    - Persistent across restarts
    - Thread-safe execution
    """

    def __init__(self, cloud_webhook: str = ""):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.handlers: Dict[str, Callable] = {}
        self._load_tasks()
        self._running = False
        self._thread = None
        self.cloud_dispatcher = CloudAgentDispatcher(default_webhook=cloud_webhook)

    def _load_tasks(self):
        """Load scheduled tasks from disk."""
        if TASKS_FILE.exists():
            try:
                data = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
                for task_data in data:
                    task = ScheduledTask.from_dict(task_data)
                    if task.enabled:
                        self.tasks[task.task_id] = task
            except Exception as e:
                print(f"[Scheduler] Failed to load tasks: {e}")

    def _save_tasks(self):
        """Save scheduled tasks to disk."""
        with LOCK:
            all_tasks = [task.to_dict() for task in self.tasks.values()]
            TASKS_FILE.write_text(json.dumps(all_tasks, indent=2), encoding="utf-8")

    def register_handler(self, action_type: str, handler: Callable):
        """Register a handler function for an action type."""
        self.handlers[action_type] = handler

    def add_task(
        self,
        name: str,
        action_type: str,
        schedule: str,
        details: Optional[Dict] = None,
        agent: str = "auto",
    ) -> ScheduledTask:
        """
        Add a new scheduled task.

        Schedule formats:
        - "every 5 minutes"
        - "every 2 hours"
        - "every 1 days"
        - "at 14:30"
        - "daily at 09:00"
        - "weekly on monday at 10:00"
        - "monthly on 1 at 00:00"
        - "once in 30 minutes"
        - "30 14 * * *" (cron: minute hour day month weekday)
        """
        task_id = f"task_{name.lower().replace(' ', '_')}_{int(time.time())}"

        task = ScheduledTask(
            task_id=task_id,
            name=name,
            action_type=action_type,
            details=details or {},
            schedule=schedule,
            agent=agent,
        )

        self.tasks[task_id] = task
        self._save_tasks()
        return task

    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
            return True
        return False

    def enable_task(self, task_id: str) -> bool:
        """Enable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self.tasks[task_id].next_run = self.tasks[task_id]._calc_next_run()
            self._save_tasks()
            return True
        return False

    def disable_task(self, task_id: str) -> bool:
        """Disable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self._save_tasks()
            return True
        return False

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def list_tasks(self, enabled_only: bool = False) -> List[Dict]:
        """List all scheduled tasks."""
        tasks = []
        for task in self.tasks.values():
            if enabled_only and not task.enabled:
                continue
            tasks.append(task.to_dict())
        tasks.sort(key=lambda t: t.get("next_run", ""))
        return tasks

    def check_and_run(self):
        """Check all tasks and run those that are due."""
        for task in self.tasks.values():
            if task.should_run():
                self._execute_task(task)

    def _execute_task(self, task: ScheduledTask):
        """Execute a single task."""
        try:
            handler = self.handlers.get(task.action_type)
            if handler:
                result = handler(task.details, task.agent)
                task.record_run(True, str(result))
            else:
                task.record_run(
                    False,
                    f"No handler registered for action type: {task.action_type}",
                )
        except Exception as e:
            task.record_run(False, str(e))

        self._save_tasks()

    def start(self, check_interval: int = 60):
        """Start the scheduler background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, args=(check_interval,), daemon=True
        )
        self._thread.start()
        print(f"[Scheduler] Started (checking every {check_interval}s)")

    def stop(self):
        """Stop the scheduler background thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[Scheduler] Stopped")

    def _run_loop(self, check_interval: int):
        """Main scheduler loop."""
        while self._running:
            try:
                self.check_and_run()
            except Exception as e:
                print(f"[Scheduler] Error in run loop: {e}")
            time.sleep(check_interval)

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        tasks = self.list_tasks()

        upcoming = []
        for task in tasks:
            if task.get("next_run") and task.get("enabled"):
                upcoming.append({
                    "name": task["name"],
                    "next_run": task["next_run"],
                    "schedule": task["schedule"],
                    "run_count": task["run_count"],
                })

        return {
            "total_tasks": len(tasks),
            "enabled_tasks": sum(1 for t in tasks if t.get("enabled")),
            "handlers_registered": list(self.handlers.keys()),
            "running": self._running,
            "upcoming": upcoming[:10],
            "cloud_agent": self.cloud_dispatcher.get_stats(),
        }


def load_scheduler(cloud_webhook: str = "") -> TaskScheduler:
    """Factory function."""
    return TaskScheduler(cloud_webhook=cloud_webhook)


if __name__ == "__main__":
    import sys
    sys.path.insert(
        0, str(Path(__file__).resolve().parent.parent)
    )

    print("=== Task Scheduler - Phase 3 ===\n")

    scheduler = load_scheduler()

    # Register a simple handler
    def mock_vault_cleanup(details, agent):
        return "Cleaned 3 stale notes"

    def mock_price_check(details, agent):
        return "Price checked: 3 products updated"

    def mock_memory_backup(details, agent):
        return "Memory backed up to disk"

    scheduler.register_handler("vault_cleanup", mock_vault_cleanup)
    scheduler.register_handler("price_check", mock_price_check)
    scheduler.register_handler("memory_backup", mock_memory_backup)

    # Add tasks with various schedules
    print("--- Adding Tasks ---")

    t1 = scheduler.add_task(
        "Vault Cleanup",
        "vault_cleanup",
        "daily at 02:00",
        agent="lais",
    )
    print(f"  Added: {t1.name} - next run: {t1.next_run}")

    t2 = scheduler.add_task(
        "Price Monitor",
        "price_check",
        "every 4 hours",
        agent="opencode",
    )
    print(f"  Added: {t2.name} - next run: {t2.next_run}")

    t3 = scheduler.add_task(
        "Memory Backup",
        "memory_backup",
        "every 30 minutes",
        agent="jarvis",
    )
    print(f"  Added: {t3.name} - next run: {t3.next_run}")

    t4 = scheduler.add_task(
        "Weekly Report",
        "vault_cleanup",
        "weekly on sunday at 20:00",
        agent="lais",
    )
    print(f"  Added: {t4.name} - next run: {t4.next_run}")

    print("\n--- Task List ---")
    tasks = scheduler.list_tasks()
    for t in tasks:
        print(f"  [{t['enabled']}] {t['name']} - {t['schedule']} (next: {t['next_run']})")

    print("\n--- Scheduler Status ---")
    status = scheduler.get_status()
    print(json.dumps(status, indent=2))

    print("\n--- Simulating Task Execution ---")
    scheduler.check_and_run()
    tasks = scheduler.list_tasks()
    for t in tasks:
        if t.get("last_run"):
            print(f"  {t['name']}: ran at {t['last_run']} - {t['last_result']}")

    print("\nPhase 3 scheduler test complete.")
