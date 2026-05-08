import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).parent.parent
PLANS_DIR = BASE_DIR / "knowledge" / "plans"

PLANS_DIR.mkdir(parents=True, exist_ok=True)


class PlanMode:
    def __init__(self):
        self.current_plan: Optional[Dict] = None
        self.undo_stack: List[Dict] = []
        self.redo_stack: List[Dict] = []
        self.plan_history: List[Dict] = []
        self._load_state()
    
    def _load_state(self):
        state_file = PLANS_DIR / "plan_state.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                self.plan_history = state.get("history", [])
                self.undo_stack = state.get("undo_stack", [])
                self.redo_stack = state.get("redo_stack", [])
            except Exception as e:
                pass
    
    def _save_state(self):
        state_file = PLANS_DIR / "plan_state.json"
        state = {
            "history": self.plan_history[-20:],
            "undo_stack": self.undo_stack,
            "redo_stack": self.redo_stack
        }
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    
    def create_plan(self, task: str, steps: List[str], rollback: Optional[List[str]] = None):
        plan = {
            "task": task,
            "steps": steps,
            "rollback": rollback or [],
            "created": datetime.now().isoformat(),
            "executed": False,
            "steps_completed": 0
        }
        self.current_plan = plan
        self.redo_stack.clear()
        return plan
    
    def show_plan(self, plan: Optional[Dict] = None) -> str:
        p = plan or self.current_plan
        if not p:
            return "No active plan."
        
        output = f"Plan: {p['task']}\n\nSteps:\n"
        for i, step in enumerate(p['steps'], 1):
            check = "[x]" if i <= p.get("steps_completed", 0) else "[ ]"
            output += f"{check} {i}. {step}\n"
        
        if p.get('rollback'):
            output += "\nRollback:\n"
            for i, step in enumerate(p['rollback'], 1):
                output += f"  {i}. {step}\n"
        
        return output
    
    def execute_plan(self) -> str:
        if not self.current_plan:
            return "No plan to execute."
        
        self.current_plan["executed"] = True
        self.current_plan["executed_at"] = datetime.now().isoformat()
        self.plan_history.append(self.current_plan)
        self.undo_stack.append(self.current_plan)
        self.redo_stack.clear()
        self._save_state()
        
        return f"Plan executed: {self.current_plan['task']}"
    
    def undo(self) -> Optional[Dict]:
        if not self.undo_stack:
            return None
        
        plan = self.undo_stack.pop()
        self.redo_stack.append(plan)
        
        if self.current_plan:
            self.plan_history.append(self.current_plan)
        
        self.current_plan = None
        self._save_state()
        
        return plan
    
    def redo(self) -> Optional[Dict]:
        if not self.redo_stack:
            return None
        
        plan = self.redo_stack.pop()
        self.undo_stack.append(plan)
        self.current_plan = plan
        self._save_state()
        
        return plan
    
    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0


def new_plan(task: str, steps: List[str], rollback: Optional[List[str]] = None):
    pm = PlanMode()
    pm.create_plan(task, steps, rollback)
    return pm.show_plan()


def show_current():
    pm = PlanMode()
    return pm.show_plan()


def execute_current():
    pm = PlanMode()
    return pm.execute_plan()


def undo_last():
    pm = PlanMode()
    plan = pm.undo()
    if plan:
        return f"Undone: {plan['task']}"
    return "Nothing to undo."


def redo_last():
    pm = PlanMode()
    plan = pm.redo()
    if plan:
        return f"Redone: {plan['task']}"
    return "Nothing to redo."


if __name__ == "__main__":
    pm = PlanMode()
    print("Plan Mode Ready")
    print(f"Can undo: {pm.can_undo()}")
    print(f"Can redo: {pm.can_redo()}")