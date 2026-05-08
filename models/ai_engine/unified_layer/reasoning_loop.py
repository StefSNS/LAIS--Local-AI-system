"""
Planning/Reasoning Loop v1.0 - ReAct Pattern Implementation
Plan → Execute → Reflect → Adjust cycle for multi-step reasoning.
Enables agents to break complex tasks into steps and self-correct.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from threading import Lock
import json


class PlanStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStep:
    """A single step in a reasoning plan."""

    def __init__(self, step_id: int, description: str, action: str = ""):
        self.step_id = step_id
        self.description = description
        self.action = action
        self.status = PlanStepStatus.PENDING
        self.result: Optional[str] = None
        self.error: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "description": self.description,
            "action": self.action,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
        }


class Plan:
    """A multi-step reasoning plan."""

    def __init__(self, goal: str, steps: list[PlanStep]):
        self.goal = goal
        self.steps = steps
        self.created_at = datetime.now()
        self.current_step = 0
        self.status = "active"
        self.reflection_history = []
        self.final_result: Optional[str] = None

    def next_step(self) -> Optional[PlanStep]:
        """Get next pending step."""
        for i, step in enumerate(self.steps):
            if step.status == PlanStepStatus.PENDING:
                self.current_step = i
                return step
        return None

    def mark_completed(self, step_id: int, result: str) -> None:
        step = self.steps[step_id]
        step.status = PlanStepStatus.COMPLETED
        step.result = result
        step.completed_at = datetime.now()

    def mark_failed(self, step_id: int, error: str) -> None:
        step = self.steps[step_id]
        step.status = PlanStepStatus.FAILED
        step.error = error
        step.completed_at = datetime.now()

    @property
    def is_complete(self) -> bool:
        return all(
            s.status in (PlanStepStatus.COMPLETED, PlanStepStatus.SKIPPED)
            for s in self.steps
        )

    @property
    def progress_pct(self) -> float:
        completed = sum(1 for s in self.steps if s.status == PlanStepStatus.COMPLETED)
        return round(completed / len(self.steps) * 100, 1) if self.steps else 0

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "steps": [s.to_dict() for s in self.steps],
            "current_step": self.current_step,
            "status": self.status,
            "progress_pct": self.progress_pct,
            "is_complete": self.is_complete,
            "reflection_history": self.reflection_history,
            "final_result": self.final_result,
        }


class ReActLoop:
    """
    Reason + Act loop for multi-step task execution.
    Pattern: Think → Act → Observe → Reflect → Repeat
    """

    def __init__(
        self,
        plan_fn=None,
        execute_fn=None,
        reflect_fn=None,
        max_iterations: int = 10,
    ):
        self.plan_fn = plan_fn
        self.execute_fn = execute_fn
        self.reflect_fn = reflect_fn
        self.max_iterations = max_iterations
        self._plans = []
        self._lock = Lock()

    def create_plan(self, goal: str, transport_chat_fn=None) -> Plan:
        """Create a plan using LLM reasoning."""
        prompt = f"""Break down this goal into concrete, executable steps. Return ONLY a JSON array of steps.

Goal: {goal}

Each step should have:
- "description": what to do
- "action": the specific action to take

Return format:
[
  {{"description": "Step 1 description", "action": "specific action"}},
  {{"description": "Step 2 description", "action": "specific action"}}
]

Limit: 5 steps maximum."""

        if transport_chat_fn:
            try:
                result = transport_chat_fn(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=512,
                )
                text = result.get("text", "")
                steps_data = self._parse_json_array(text)
                if steps_data:
                    steps = [
                        PlanStep(i + 1, s.get("description", ""), s.get("action", ""))
                        for i, s in enumerate(steps_data)
                    ]
                    plan = Plan(goal, steps)
                    with self._lock:
                        self._plans.append(plan)
                    return plan
            except Exception as e:
                print(f"[ReAct] Plan creation error: {e}")

        steps = [PlanStep(1, goal, goal)]
        plan = Plan(goal, steps)
        with self._lock:
            self._plans.append(plan)
        return plan

    def execute_plan(
        self,
        plan: Plan,
        transport_chat_fn=None,
    ) -> Plan:
        """Execute plan steps with reflection between each."""
        iteration = 0

        while not plan.is_complete and iteration < self.max_iterations:
            step = plan.next_step()
            if not step:
                break

            step.status = PlanStepStatus.RUNNING
            step.started_at = datetime.now()

            try:
                result = self._execute_step(step, plan, transport_chat_fn)

                if self.reflect_fn:
                    reflection = self.reflect_fn(step, result, plan)
                    plan.reflection_history.append(reflection)
                    if reflection.get("retry", False):
                        step.status = PlanStepStatus.PENDING
                        iteration += 1
                        continue

                plan.mark_completed(step.step_id - 1, str(result))

            except Exception as e:
                plan.mark_failed(step.step_id - 1, str(e))

            iteration += 1

        if plan.is_complete:
            plan.status = "completed"
            plan.final_result = self._synthesize_result(plan)
        else:
            plan.status = "incomplete"

        return plan

    def react_query(
        self,
        query: str,
        transport_chat_fn=None,
        max_steps: int = 5,
    ) -> dict:
        """
        Full ReAct cycle for a single query.
        Think → Act → Observe → Reflect → Answer
        """
        plan = self.create_plan(query, transport_chat_fn)

        if transport_chat_fn:
            plan = self.execute_plan(plan, transport_chat_fn)

        return {
            "query": query,
            "plan": plan.to_dict(),
            "answer": plan.final_result or "Execution incomplete",
            "steps_taken": sum(1 for s in plan.steps if s.status == PlanStepStatus.COMPLETED),
            "iterations": len(plan.reflection_history),
        }

    def _execute_step(
        self,
        step: PlanStep,
        plan: Plan,
        transport_chat_fn=None,
    ) -> str:
        if not transport_chat_fn:
            return f"Executed: {step.action}"

        context = self._get_step_context(step, plan)
        prompt = f"""Execute this step of the plan:

Plan goal: {plan.goal}
Current step: {step.description}
Action: {step.action}
Previous context: {context}

Execute the action and return the result. Be specific and factual."""

        result = transport_chat_fn(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1024,
        )
        return result.get("text", "")

    def _get_step_context(self, step: PlanStep, plan: Plan) -> str:
        context_parts = []
        for s in plan.steps:
            if s.step_id < step.step_id and s.status == PlanStepStatus.COMPLETED:
                context_parts.append(f"Step {s.step_id}: {s.result}")
        return "\n".join(context_parts) if context_parts else "No previous steps completed."

    def _synthesize_result(self, plan: Plan) -> str:
        completed = [s for s in plan.steps if s.status == PlanStepStatus.COMPLETED]
        if not completed:
            return "No steps completed"

        parts = []
        for s in completed:
            if s.result:
                parts.append(f"Step {s.step_id} ({s.description}): {s.result[:200]}")

        return "\n".join(parts)

    def _parse_json_array(self, text: str) -> list:
        try:
            text = text.strip()
            if text.startswith("```"):
                text = text.split("```", 2)[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()
            return json.loads(text)
        except Exception:
            import re
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
            return []

    def get_plan_history(self) -> list[dict]:
        return [p.to_dict() for p in self._plans]


_global_react: Optional[ReActLoop] = None
_react_lock = Lock()


def get_react_loop(
    plan_fn=None,
    execute_fn=None,
    reflect_fn=None,
) -> ReActLoop:
    global _global_react
    if _global_react is None:
        with _react_lock:
            if _global_react is None:
                _global_react = ReActLoop(plan_fn, execute_fn, reflect_fn)
    return _global_react
