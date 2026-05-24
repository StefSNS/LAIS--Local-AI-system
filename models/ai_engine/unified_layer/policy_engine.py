"""
Human-on-the-Loop Policy Engine v1.0
Implements autonomy levels 1-5 for agent operations.
Replaces per-action approvals with graduated autonomy controls.
"""

from datetime import datetime
from enum import IntEnum
from typing import Optional, Callable
from threading import Lock
import json


class AutonomyLevel(IntEnum):
    LEVEL_1_OBSERVE = 1
    LEVEL_2_SUGGEST = 2
    LEVEL_3_APPROVE_ACTIONS = 3
    LEVEL_4_APPROVE_CATEGORIES = 4
    LEVEL_5_FULL_AUTONOMY = 5


AUTONOMY_DESCRIPTIONS = {
    AutonomyLevel.LEVEL_1_OBSERVE: "Agent only observes and reports. No actions taken.",
    AutonomyLevel.LEVEL_2_SUGGEST: "Agent suggests actions. Human must approve each.",
    AutonomyLevel.LEVEL_3_APPROVE_ACTIONS: "Agent executes low-risk actions. High-risk requires approval.",
    AutonomyLevel.LEVEL_4_APPROVE_CATEGORIES: "Agent executes approved categories. New categories need approval.",
    AutonomyLevel.LEVEL_5_FULL_AUTONOMY: "Full autonomy. Agent executes all actions within scope.",
}


class RiskLevel(IntEnum):
    SAFE = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    CRITICAL = 5


class PolicyAction:
    """Represents a proposed action for policy evaluation."""

    def __init__(
        self,
        action_type: str,
        description: str,
        risk_level: RiskLevel = RiskLevel.LOW,
        parameters: Optional[dict] = None,
    ):
        self.action_type = action_type
        self.description = description
        self.risk_level = risk_level
        self.parameters = parameters or {}
        self.timestamp = datetime.now()


class PolicyDecision:
    """Result of policy evaluation."""

    def __init__(
        self,
        approved: bool,
        reason: str = "",
        requires_human: bool = False,
        modified_action: Optional[dict] = None,
    ):
        self.approved = approved
        self.reason = reason
        self.requires_human = requires_human
        self.modified_action = modified_action


class AutonomyPolicy:
    """
    Defines what actions are allowed at each autonomy level.
    """

    def __init__(self):
        self.allowed_actions = {
            AutonomyLevel.LEVEL_1_OBSERVE: set(),
            AutonomyLevel.LEVEL_2_SUGGEST: set(),
            AutonomyLevel.LEVEL_3_APPROVE_ACTIONS: {"read", "search", "analyze", "summarize"},
            AutonomyLevel.LEVEL_4_APPROVE_CATEGORIES: {
                "read", "search", "analyze", "summarize",
                "write", "create", "update", "delete",
            },
            AutonomyLevel.LEVEL_5_FULL_AUTONOMY: None,
        }

        self.risk_thresholds = {
            AutonomyLevel.LEVEL_1_OBSERVE: 0,
            AutonomyLevel.LEVEL_2_SUGGEST: 0,
            AutonomyLevel.LEVEL_3_APPROVE_ACTIONS: 2,
            AutonomyLevel.LEVEL_4_APPROVE_CATEGORIES: 3,
            AutonomyLevel.LEVEL_5_FULL_AUTONOMY: 5,
        }

    def can_execute(self, action: PolicyAction, level: AutonomyLevel) -> PolicyDecision:
        allowed = self.allowed_actions.get(level)

        if allowed is None:
            return PolicyDecision(approved=True, reason="Full autonomy")

        if action.action_type in allowed and action.risk_level <= self.risk_thresholds.get(level, 0):
            return PolicyDecision(approved=True, reason=f"Allowed at level {level}")

        if action.risk_level > self.risk_thresholds.get(level, 0):
            return PolicyDecision(
                approved=False,
                requires_human=True,
                reason=f"Risk level {action.risk_level} exceeds threshold for level {level}",
            )

        return PolicyDecision(
            approved=False,
            requires_human=True,
            reason=f"Action type '{action.action_type}' not allowed at level {level}",
        )


class HumanOnTheLoopEngine:
    """
    Manages autonomy levels and enforces policy decisions.
    """

    def __init__(self):
        self._autonomy_level = AutonomyLevel.LEVEL_3_APPROVE_ACTIONS
        self._policy = AutonomyPolicy()
        self._approval_callbacks = []
        self._audit_log = []
        self._lock = Lock()

    @property
    def autonomy_level(self) -> AutonomyLevel:
        return self._autonomy_level

    def set_autonomy_level(self, level: AutonomyLevel) -> dict:
        with self._lock:
            old_level = self._autonomy_level
            self._autonomy_level = level
            self._log_event("level_change", {
                "from": old_level.value,
                "to": level.value,
                "description": AUTONOMY_DESCRIPTIONS[level],
            })
            return {
                "success": True,
                "level": level.value,
                "description": AUTONOMY_DESCRIPTIONS[level],
            }

    def evaluate_action(self, action: PolicyAction) -> PolicyDecision:
        decision = self._policy.can_execute(action, self._autonomy_level)

        self._log_event("action_eval", {
            "action_type": action.action_type,
            "risk_level": action.risk_level.value,
            "approved": decision.approved,
            "requires_human": decision.requires_human,
        })

        if decision.requires_human:
            for callback in self._approval_callbacks:
                try:
                    callback(action, decision)
                except Exception:
                    pass

        return decision

    def add_approval_callback(self, callback: Callable) -> None:
        self._approval_callbacks.append(callback)

    def get_audit_log(self, limit: int = 50) -> list[dict]:
        with self._lock:
            return self._audit_log[-limit:]

    def get_status(self) -> dict:
        return {
            "autonomy_level": self._autonomy_level.value,
            "description": AUTONOMY_DESCRIPTIONS[self._autonomy_level],
            "audit_entries": len(self._audit_log),
            "callbacks": len(self._approval_callbacks),
        }

    def _log_event(self, event_type: str, data: dict) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
        }
        self._audit_log.append(entry)


_global_engine: Optional[HumanOnTheLoopEngine] = None
_engine_lock = Lock()


def get_autonomy_engine() -> HumanOnTheLoopEngine:
    global _global_engine
    if _global_engine is None:
        with _engine_lock:
            if _global_engine is None:
                _global_engine = HumanOnTheLoopEngine()
    return _global_engine
