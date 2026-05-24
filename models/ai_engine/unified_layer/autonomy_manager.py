"""
Autonomy Manager - Phase 2 of Architecture Evolution
Manages autonomy levels, tracks approvals, and provides audit logging.
Coordinates between agents and the security policy.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from threading import Lock

import sys
from pathlib import Path

try:
    from .security_policy import (
        SecurityPolicy, load_security_policy,
        AutonomyLevel, RiskLevel
    )
except ImportError:
    lais_path = str(Path(__file__).resolve().parent.parent)
    if lais_path not in sys.path:
        sys.path.insert(0, lais_path)
    from unified_layer.security_policy import (
        SecurityPolicy, load_security_policy,
        AutonomyLevel, RiskLevel
    )

APPROVAL_LOG_PATH = Path(
    Path(__file__).resolve().parent.parent / "knowledge" / "memory" / "approval_log.json"
)
APPROVAL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
LOCK = Lock()


class ApprovalRequest:
    """Represents a pending approval request."""

    def __init__(
        self,
        agent: str,
        action_type: str,
        risk_level: str,
        details: Dict[str, Any],
        reason: str,
    ):
        self.id = f"approval_{agent}_{int(datetime.now().timestamp())}"
        self.agent = agent
        self.action_type = action_type
        self.risk_level = risk_level
        self.details = details
        self.reason = reason
        self.timestamp = datetime.now().isoformat()
        self.status = "pending"
        self.resolved_at = None
        self.resolved_by = None

    def approve(self, resolver: str = "user"):
        self.status = "approved"
        self.resolved_at = datetime.now().isoformat()
        self.resolved_by = resolver

    def deny(self, resolver: str = "user"):
        self.status = "denied"
        self.resolved_at = datetime.now().isoformat()
        self.resolved_by = resolver

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent": self.agent,
            "action_type": self.action_type,
            "risk_level": self.risk_level,
            "details": self.details,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "status": self.status,
            "resolved_at": self.resolved_at,
            "resolved_by": self.resolved_by,
        }


class AutonomyManager:
    """
    Manages autonomy levels and approval workflow across all agents.
    """

    def __init__(self):
        self.policies: Dict[str, SecurityPolicy] = {}
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self._load_approval_log()

    def _load_approval_log(self):
        """Load pending approvals from disk."""
        if APPROVAL_LOG_PATH.exists():
            try:
                data = json.loads(APPROVAL_LOG_PATH.read_text(encoding="utf-8"))
                for req_data in data:
                    if req_data.get("status") == "pending":
                        req = ApprovalRequest(
                            agent=req_data["agent"],
                            action_type=req_data["action_type"],
                            risk_level=req_data["risk_level"],
                            details=req_data.get("details", {}),
                            reason=req_data.get("reason", ""),
                        )
                        req.id = req_data["id"]
                        req.timestamp = req_data["timestamp"]
                        self.pending_approvals[req.id] = req
            except Exception:
                pass

    def _save_approval_log(self):
        """Save approval log to disk."""
        with LOCK:
            all_requests = [req.to_dict() for req in self.pending_approvals.values()]
            APPROVAL_LOG_PATH.write_text(
                json.dumps(all_requests[-100:], indent=2),
                encoding="utf-8",
            )

    def get_policy(self, agent_name: str) -> SecurityPolicy:
        """Get or create security policy for an agent."""
        if agent_name not in self.policies:
            self.policies[agent_name] = load_security_policy(agent_name)
        return self.policies[agent_name]

    def check_action(
        self,
        agent_name: str,
        action_type: str,
        details: Optional[Dict] = None,
        cost: float = 0.0,
    ) -> Tuple[bool, str, Optional[ApprovalRequest]]:
        """
        Check if an agent can perform an action.
        Returns (allowed, reason, approval_request_if_needed).
        """
        policy = self.get_policy(agent_name)

        # Full approval check
        allowed, reason = policy.can_proceed(action_type, details, cost)

        if allowed:
            return True, reason, None

        # Check if this is an approval-needed case vs a hard block
        approval_info = policy.get_pending_approvals(action_type, details)

        if approval_info:
            req = ApprovalRequest(
                agent=agent_name,
                action_type=action_type,
                risk_level=approval_info["risk_level"],
                details=approval_info.get("details", {}),
                reason=approval_info["reason"],
            )
            self.pending_approvals[req.id] = req
            self._save_approval_log()
            return False, f"Requires approval: {reason}", req

        return False, reason, None

    def approve_action(self, request_id: str, resolver: str = "user") -> bool:
        """Approve a pending request."""
        if request_id not in self.pending_approvals:
            return False

        req = self.pending_approvals[request_id]
        req.approve(resolver)
        self._save_approval_log()
        return True

    def deny_action(self, request_id: str, resolver: str = "user") -> bool:
        """Deny a pending request."""
        if request_id not in self.pending_approvals:
            return False

        req = self.pending_approvals[request_id]
        req.deny(resolver)
        self._save_approval_log()
        return True

    def get_pending_requests(self, agent: Optional[str] = None) -> List[Dict]:
        """Get all pending approval requests."""
        requests = []
        for req in self.pending_approvals.values():
            if req.status == "pending":
                if agent is None or req.agent == agent:
                    requests.append(req.to_dict())
        return requests

    def set_autonomy_level(self, agent_name: str, level: str) -> bool:
        """Change autonomy level for an agent."""
        try:
            AutonomyLevel(level)
        except ValueError:
            return False

        policy = self.get_policy(agent_name)
        policy.set_autonomy_level(level)
        return True

    def get_system_status(self) -> Dict[str, Any]:
        """Get full system autonomy status."""
        status = {}
        for agent_name, policy in self.policies.items():
            status[agent_name] = policy.get_status()

        pending = self.get_pending_requests()

        return {
            "agents": status,
            "pending_approvals": len(pending),
            "pending_requests": pending,
        }

    def audit_log(self) -> List[Dict]:
        """Get full audit log of all approval decisions."""
        if APPROVAL_LOG_PATH.exists():
            try:
                return json.loads(APPROVAL_LOG_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []


def load_autonomy_manager() -> AutonomyManager:
    """Factory function."""
    return AutonomyManager()


if __name__ == "__main__":
    import sys
    sys.path.insert(
        0, str(Path(__file__).resolve().parent.parent)
    )

    print("=== Autonomy Manager - Phase 2 ===\n")

    manager = load_autonomy_manager()

    # Test actions across agents
    agents_actions = [
        ("lais", "vault_read", {}),
        ("lais", "vault_write", {"path": "test.md"}),
        ("lais", "file_delete", {"path": "old_note.md"}),
        ("jarvis", "memory_read", {}),
        ("jarvis", "memory_write", {}),
        ("jarvis", "network_external", {"url": "https://api.example.com"}),
        ("opencode", "code_execute", {"command": "python test.py"}),
        ("opencode", "process_kill", {"command": "taskkill /f /pid 1234"}),
        ("opencode", "api_call_paid", {"service": "openrouter"}),
    ]

    for agent, action, details in agents_actions:
        allowed, reason, req = manager.check_action(agent, action, details)
        if req:
            print(f"  [PENDING] {agent}/{action}: {reason} (id: {req.id})")
        elif allowed:
            print(f"  [OK] {agent}/{action}")
        else:
            print(f"  [BLOCKED] {agent}/{action}: {reason}")

    print("\n--- System Status ---")
    status = manager.get_system_status()
    print(f"Agents configured: {len(status['agents'])}")
    print(f"Pending approvals: {status['pending_approvals']}")

    for agent, info in status["agents"].items():
        print(f"\n  {agent}:")
        print(f"    Autonomy: {info['autonomy_level']}")
        print(f"    Rate: {info['rate_usage']['actions_last_hour']}/{info['rate_usage']['actions_limit']} actions/hour")

    print("\n--- Audit Log ---")
    log = manager.audit_log()
    print(f"Total entries: {len(log)}")
    if log:
        for entry in log[-3:]:
            print(f"  [{entry['status']}] {entry['agent']}/{entry['action_type']}")
