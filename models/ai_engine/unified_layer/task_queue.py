"""
Task Queue / Orchestration - Shared queue for agent delegation
Allows agents to submit tasks and pick up work based on capabilities.
"""

import json
import os
import time
import uuid
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from threading import Lock

QUEUE_DIR = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\sync")
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

TASK_QUEUE_FILE = QUEUE_DIR / "task_queue.json"
TASK_LOG_FILE = QUEUE_DIR / "task_log.json"
DASHBOARD_FLAG_FILE = QUEUE_DIR / "dashboard_running.flag"
LOCK = Lock()

AGENT_CAPABILITIES = {
    "lais": ["research", "analysis", "writing", "planning", "general"],
    "jarvis": ["voice", "real-time", "scheduling", "communication", "system-control", "general"],
    "opencode": ["coding", "review", "refactor", "debug", "architecture", "general"]
}

TASK_PRIORITIES = {"low": 0, "normal": 1, "high": 2, "urgent": 3}


class TaskQueue:
    """Shared task queue for agent orchestration."""
    
    def __init__(self):
        self.queue = self._load()
    
    def _load(self):
        """Load task queue from disk."""
        if TASK_QUEUE_FILE.exists():
            try:
                return json.loads(TASK_QUEUE_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                return {"tasks": [], "completed": []}
        return {"tasks": [], "completed": []}
    
    def _save(self):
        """Save task queue to disk."""
        with LOCK:
            TASK_QUEUE_FILE.write_text(
                json.dumps(self.queue, indent=2),
                encoding="utf-8"
            )
    
    def _is_dashboard_running(self):
        """Check if dashboard flag file exists and is recent."""
        if DASHBOARD_FLAG_FILE.exists():
            try:
                flag_time = DASHBOARD_FLAG_FILE.stat().st_mtime
                return (time.time() - flag_time) < 300
            except Exception as e:
                pass
        return False
    
    def _launch_dashboard(self):
        """Launch dashboard in background if not already running."""
        if self._is_dashboard_running():
            return
        
        dashboard_path = Path(__file__).parent / "dashboard.py"
        if not dashboard_path.exists():
            return
        
        try:
            subprocess.Popen(
                [sys.executable, str(dashboard_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            DASHBOARD_FLAG_FILE.write_text(datetime.now().isoformat(), encoding="utf-8")
            print(f"[TaskQueue] Dashboard launched at http://127.0.0.1:8888")
        except Exception as e:
            print(f"[TaskQueue] Failed to launch dashboard: {e}")
    
    def submit_task(self, agent, title, description, task_type="general", priority="normal", 
                    assigned_to=None, requires=[], context=None):
        """
        Submit a new task to the queue.
        agent: submitting agent
        title: task title
        description: detailed description
        task_type: category of task (research/coding/voice/etc)
        priority: low/normal/high/urgent
        assigned_to: specific agent to handle (None = auto-assign)
        requires: list of required capabilities
        context: additional context data
        """
        task = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "description": description,
            "type": task_type,
            "priority": priority,
            "status": "pending",
            "submitted_by": agent,
            "assigned_to": assigned_to or self._auto_assign(task_type, requires),
            "requires": requires,
            "context": context or {},
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "started": None,
            "completed": None,
            "result": None
        }
        
        self.queue["tasks"].append(task)
        self._log_task(task["id"], "created", agent)
        self._save()
        
        if len(self.queue["tasks"]) == 1:
            self._launch_dashboard()
        
        return task["id"]
    
    def _auto_assign(self, task_type, requires):
        """Auto-assign task to best suited agent."""
        scores = {}
        
        for agent, capabilities in AGENT_CAPABILITIES.items():
            score = 0
            if task_type in capabilities:
                score += 10
            for req in requires:
                if req in capabilities:
                    score += 5
            scores[agent] = score
        
        if scores:
            return max(scores, key=scores.get)
        return "lais"
    
    def claim_task(self, agent, task_id=None):
        """
        Agent claims a task from the queue.
        If task_id provided, claim specific task.
        Otherwise, claim highest priority pending task they can handle.
        """
        capabilities = AGENT_CAPABILITIES.get(agent, [])
        
        if task_id:
            for task in self.queue["tasks"]:
                if task["id"] == task_id and task["status"] == "pending":
                    task["status"] = "in_progress"
                    task["assigned_to"] = agent
                    task["started"] = datetime.now().isoformat()
                    task["updated"] = datetime.now().isoformat()
                    self._log_task(task_id, "claimed", agent)
                    self._save()
                    return task
            return None
        
        pending = [t for t in self.queue["tasks"] 
                   if t["status"] == "pending" and 
                   (t["assigned_to"] == agent or t["assigned_to"] is None)]
        
        if not pending:
            return None
        
        pending.sort(key=lambda t: TASK_PRIORITIES.get(t["priority"], 1), reverse=True)
        task = pending[0]
        task["status"] = "in_progress"
        task["assigned_to"] = agent
        task["started"] = datetime.now().isoformat()
        task["updated"] = datetime.now().isoformat()
        
        self._log_task(task["id"], "claimed", agent)
        self._save()
        
        return task
    
    def complete_task(self, agent, task_id, result=None):
        """Mark a task as completed."""
        for task in self.queue["tasks"]:
            if task["id"] == task_id and task["status"] == "in_progress":
                task["status"] = "completed"
                task["completed"] = datetime.now().isoformat()
                task["updated"] = datetime.now().isoformat()
                task["result"] = result
                
                self.queue["tasks"].remove(task)
                self.queue["completed"].append(task)
                self.queue["completed"] = self.queue["completed"][-100:]
                
                self._log_task(task_id, "completed", agent)
                self._save()
                return True
        return False
    
    def get_pending_tasks(self, agent=None):
        """Get pending tasks, optionally filtered by agent."""
        tasks = [t for t in self.queue["tasks"] if t["status"] == "pending"]
        if agent:
            tasks = [t for t in tasks if t["assigned_to"] == agent or t["assigned_to"] is None]
        tasks.sort(key=lambda t: TASK_PRIORITIES.get(t["priority"], 1), reverse=True)
        return tasks
    
    def get_active_tasks(self, agent=None):
        """Get in-progress tasks."""
        tasks = [t for t in self.queue["tasks"] if t["status"] == "in_progress"]
        if agent:
            tasks = [t for t in tasks if t["assigned_to"] == agent]
        return tasks
    
    def get_queue_status(self):
        """Get queue statistics."""
        return {
            "pending": len([t for t in self.queue["tasks"] if t["status"] == "pending"]),
            "in_progress": len([t for t in self.queue["tasks"] if t["status"] == "in_progress"]),
            "completed": len(self.queue["completed"]),
            "agents": {agent: {
                "pending": len([t for t in self.queue["tasks"] if t["assigned_to"] == agent and t["status"] == "pending"]),
                "active": len([t for t in self.queue["tasks"] if t["assigned_to"] == agent and t["status"] == "in_progress"])
            } for agent in AGENT_CAPABILITIES}
        }
    
    def _log_task(self, task_id, action, agent):
        """Log task action."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "action": action,
            "agent": agent
        }
        
        try:
            if TASK_LOG_FILE.exists():
                log = json.loads(TASK_LOG_FILE.read_text(encoding="utf-8"))
            else:
                log = []
            
            log.append(log_entry)
            TASK_LOG_FILE.write_text(json.dumps(log[-200:], indent=2), encoding="utf-8")
            except Exception as e:
                pass

def load_task_queue():
    """Factory function."""
    return TaskQueue()


if __name__ == "__main__":
    queue = load_task_queue()
    
    print("=== Task Queue / Orchestration ===")
    status = queue.get_queue_status()
    print(f"Pending: {status['pending']}")
    print(f"In Progress: {status['in_progress']}")
    print(f"Completed: {status['completed']}")
    
    print("\n=== Test: Submit Tasks ===")
    id1 = queue.submit_task("lais", "Research Python async", "Find best practices for async Python", "research", "normal")
    id2 = queue.submit_task("jarvis", "Schedule meeting", "Set up meeting for tomorrow 3pm", "scheduling", "high")
    id3 = queue.submit_task("opencode", "Refactor auth module", "Clean up authentication code", "coding", "urgent")
    
    print(f"  Created: {id1}, {id2}, {id3}")
    
    print("\n=== Check Assignments ===")
    for t in queue.queue["tasks"]:
        print(f"  {t['id']}: {t['title']} -> assigned to {t['assigned_to']}")
    
    print("\n=== Test: Claim Tasks ===")
    task = queue.claim_task("opencode")
    if task:
        print(f"  Opencode claimed: {task['title']} (priority: {task['priority']})")
        print(f"\n=== Test: Complete Task ===")
        queue.complete_task("opencode", task["id"], "Refactored successfully")
        print(f"  Completed: {task['title']}")
    else:
        print("  No tasks available for opencode")
        print("\n=== Test: Complete Task ===")
        print("  Skipped (no task claimed)")
    
    print("\n=== Test: Queue Status ===")
    status = queue.get_queue_status()
    print(f"  Pending: {status['pending']}")
    print(f"  In Progress: {status['in_progress']}")
    print(f"  Completed: {status['completed']}")
    print(f"  Agent loads: {status['agents']}")
