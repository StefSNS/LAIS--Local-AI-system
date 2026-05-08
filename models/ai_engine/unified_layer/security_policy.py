"""
Security Policy - Phase 2 of Architecture Evolution
Risk classification, approval gating, command validation, and rate limiting.
Inspired by ZeroClaw's security model.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from threading import Lock


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


class AutonomyLevel(Enum):
    READ_ONLY = "read_only"
    SUPERVISED = "supervised"
    FULL = "full"


CONFIG_PATH = Path(
    r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis\config.json"
)
RATE_LOG_PATH = Path(
    r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\memory\rate_log.json"
)
RATE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
LOCK = Lock()

# Risk classification rules
RISK_RULES = {
    # File operations
    "file_read": RiskLevel.LOW,
    "file_write": RiskLevel.MEDIUM,
    "file_delete": RiskLevel.HIGH,
    "file_write_system": RiskLevel.BLOCKED,
    "dir_list": RiskLevel.LOW,
    "dir_create": RiskLevel.LOW,

    # Code operations
    "code_generate": RiskLevel.LOW,
    "code_execute": RiskLevel.MEDIUM,
    "code_execute_with_imports": RiskLevel.HIGH,
    "code_modify_existing": RiskLevel.MEDIUM,

    # System operations
    "execute_safe": RiskLevel.LOW,
    "execute_destructive": RiskLevel.BLOCKED,
    "process_list": RiskLevel.LOW,
    "process_kill": RiskLevel.HIGH,
    "service_start": RiskLevel.HIGH,
    "service_stop": RiskLevel.HIGH,

    # Network operations
    "network_internal": RiskLevel.LOW,
    "network_external": RiskLevel.MEDIUM,
    "api_call_free": RiskLevel.LOW,
    "api_call_paid": RiskLevel.HIGH,

    # Memory operations
    "memory_read": RiskLevel.LOW,
    "memory_write": RiskLevel.LOW,
    "memory_delete": RiskLevel.MEDIUM,
    "vault_read": RiskLevel.LOW,
    "vault_write": RiskLevel.MEDIUM,
    "vault_delete": RiskLevel.HIGH,

    # Agent operations
    "agent_query": RiskLevel.LOW,
    "agent_delegate": RiskLevel.MEDIUM,
    "agent_modify": RiskLevel.HIGH,
}

# Commands that are always allowed
SAFE_COMMANDS = {
    "dir", "ls", "type", "cat", "echo", "where", "which",
    "pwd", "cd", "ls -la", "ls -R",
    "python -V", "python --version",
    "pip list", "pip show",
    "git status", "git log", "git branch", "git diff",
    "ipconfig", "ping", "netstat -an",
    "tasklist", "systeminfo", "hostname",
}

# Actions that don't count toward rate limit (reads/observations)
FREE_ACTIONS = {
    "file_read", "dir_list", "memory_read", "vault_read",
    "agent_query", "network_internal", "api_call_free",
    "code_generate", "process_list", "execute_safe",
}

# Commands that are always blocked
BLOCKED_COMMANDS = {
    "format", "diskpart", "del /s", "rmdir /s",
    "rm -rf", "shutdown", "restart", "reg delete",
    "net user", "netsh", "schtasks /delete",
    "taskkill /f", "wmic process call delete",
    "powershell -encodedcommand",
    "certutil", "bitsadmin",
}

# Paths that are always blocked
BLOCKED_PATH_PATTERNS = [
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\ProgramData",
    r"%USERPROFILE%\AppData",
    r"C:\boot.ini",
    r"C:\pagefile.sys",
    r"C:\hiberfil.sys",
]


class RateLimiter:
    """Tracks and limits actions per agent per time window."""

    def __init__(self, max_actions_per_hour: int = 100, max_cost_per_day: float = 0.0):
        self.max_actions = max_actions_per_hour
        self.max_cost = max_cost_per_day
        self.actions: Dict[str, List[float]] = {}
        self.costs: Dict[str, List[Tuple[float, float]]] = {}

        self._load_log()

    def _load_log(self):
        """Load rate log from disk."""
        if RATE_LOG_PATH.exists():
            try:
                data = json.loads(RATE_LOG_PATH.read_text(encoding="utf-8"))
                now = time.time()
                one_hour_ago = now - 3600
                one_day_ago = now - 86400

                for agent, timestamps in data.get("actions", {}).items():
                    self.actions[agent] = [
                        t for t in timestamps if t > one_hour_ago
                    ]

                for agent, cost_entries in data.get("costs", {}).items():
                    self.costs[agent] = [
                        (t, c) for t, c in cost_entries if t > one_day_ago
                    ]
            except Exception:
                pass

    def _save_log(self):
        """Save rate log to disk."""
        data = {
            "actions": self.actions,
            "costs": self.costs,
            "updated": datetime.now().isoformat(),
        }
        RATE_LOG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def check_action(self, agent: str) -> Tuple[bool, str]:
        """
        Check if an agent can perform an action.
        Returns (allowed, reason).
        """
        now = time.time()
        one_hour_ago = now - 3600

        agent_actions = self.actions.get(agent, [])
        agent_actions = [t for t in agent_actions if t > one_hour_ago]
        self.actions[agent] = agent_actions

        if len(agent_actions) >= self.max_actions:
            return False, f"Rate limit exceeded: {len(agent_actions)}/{self.max_actions} actions/hour"

        return True, "OK"

    def record_action(self, agent: str, cost: float = 0.0):
        """Record an action for rate limiting."""
        now = time.time()

        if agent not in self.actions:
            self.actions[agent] = []
        self.actions[agent].append(now)

        if cost > 0:
            if agent not in self.costs:
                self.costs[agent] = []
            self.costs[agent].append((now, cost))

        # Clean old entries periodically
        if len(self.actions[agent]) % 10 == 0:
            self._save_log()

    def get_usage(self, agent: str) -> Dict[str, Any]:
        """Get current usage stats for an agent."""
        now = time.time()
        one_hour_ago = now - 3600
        one_day_ago = now - 86400

        agent_actions = [
            t for t in self.actions.get(agent, []) if t > one_hour_ago
        ]
        agent_costs = [
            c for t, c in self.costs.get(agent, []) if t > one_day_ago
        ]

        return {
            "actions_last_hour": len(agent_actions),
            "actions_limit": self.max_actions,
            "cost_last_day": sum(agent_costs),
            "cost_limit": self.max_cost,
        }


class SecurityPolicy:
    """
    Security policy for agent actions.
    - Risk classification
    - Approval gating based on autonomy level
    - Command validation
    - Path validation
    - Rate limiting
    """

    def __init__(self, agent_name: str = "agent"):
        self.agent_name = agent_name
        self.config = self._load_config()

        autonomy_cfg = self.config.get("autonomy", {})
        self.autonomy_level = AutonomyLevel(
            autonomy_cfg.get(agent_name, autonomy_cfg.get("default_level", "supervised"))
        )

        security_cfg = self.config.get("security", {})
        self.rate_limiter = RateLimiter(
            max_actions_per_hour=security_cfg.get("rate_limit_actions_per_hour", 100),
            max_cost_per_day=security_cfg.get("rate_limit_cost_per_day", 0.0),
        )

        self.blocked_paths = security_cfg.get(
            "blocked_paths", BLOCKED_PATH_PATTERNS
        )
        self.allowed_patterns = security_cfg.get(
            "allowed_command_patterns", []
        )
        self.require_approval = set(
            security_cfg.get("require_approval_for", [])
        )

    def _load_config(self) -> Dict:
        """Load config.json."""
        if CONFIG_PATH.exists():
            try:
                return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def classify_risk(self, action_type: str, details: Optional[Dict] = None) -> RiskLevel:
        """
        Classify the risk level of an action.
        Returns RiskLevel enum.
        """
        risk = RISK_RULES.get(action_type, RiskLevel.MEDIUM)

        # Check for blocked commands
        if details:
            command = details.get("command", "")
            path = details.get("path", "")

            if any(cmd.lower() in command.lower() for cmd in BLOCKED_COMMANDS):
                return RiskLevel.BLOCKED

            if self._is_blocked_path(path):
                return RiskLevel.BLOCKED

        return risk

    def _is_blocked_path(self, path: str) -> bool:
        """Check if a path is in the blocked list."""
        if not path:
            return False
        path_lower = path.lower()
        return any(bp.lower() in path_lower for bp in self.blocked_paths)

    def check_approval(self, action_type: str, details: Optional[Dict] = None) -> Tuple[bool, str, RiskLevel]:
        """
        Check if an action needs approval based on autonomy level.
        Returns (approved, reason, risk_level).
        """
        risk = self.classify_risk(action_type, details)

        if risk == RiskLevel.BLOCKED:
            return False, f"Action '{action_type}' is blocked by security policy", risk

        if self.autonomy_level == AutonomyLevel.READ_ONLY:
            if risk == RiskLevel.LOW and action_type.startswith(("file_read", "dir_", "memory_read", "vault_read", "agent_query")):
                return True, "OK", risk
            return False, f"Read-only mode: cannot perform '{action_type}'", risk

        if self.autonomy_level == AutonomyLevel.SUPERVISED:
            if action_type in self.require_approval or risk in (RiskLevel.HIGH, RiskLevel.BLOCKED):
                return False, f"Approval required for '{action_type}' (risk: {risk.value})", risk
            if risk == RiskLevel.BLOCKED:
                return False, f"Action '{action_type}' is blocked", risk
            return True, "OK", risk

        if self.autonomy_level == AutonomyLevel.FULL:
            if risk == RiskLevel.BLOCKED:
                return False, f"Action '{action_type}' is blocked even in full autonomy", risk
            return True, "OK", risk

        return True, "OK", risk

    def validate_command(self, command: str) -> Tuple[bool, str]:
        """
        Validate a shell command for safety.
        Returns (allowed, reason).
        """
        cmd_lower = command.lower().strip()

        # Check blocked commands
        if any(bc in cmd_lower for bc in BLOCKED_COMMANDS):
            return False, f"Command contains blocked pattern"

        # Check blocked paths
        if self._is_blocked_path(command):
            return False, f"Command accesses a blocked path"

        # Safe commands pass automatically
        if cmd_lower in SAFE_COMMANDS or any(
            cmd_lower.startswith(safe) for safe in SAFE_COMMANDS
        ):
            return True, "OK"

        # Check allowed patterns
        if any(pat.lower() in cmd_lower for pat in self.allowed_patterns):
            return True, "OK"

        # Default: allow but log (supervised mode will catch via risk classification)
        return True, "OK (logged)"

    def record_action(self, cost: float = 0.0):
        """Record an action for rate limiting."""
        self.rate_limiter.record_action(self.agent_name, cost)

    def can_proceed(self, action_type: str, details: Optional[Dict] = None, cost: float = 0.0) -> Tuple[bool, str]:
        """
        Full check: rate limit + risk + approval.
        Returns (allowed, reason).
        """
        # Read/observation actions don't count toward rate limit
        if action_type in FREE_ACTIONS:
            approved, reason, risk = self.check_approval(action_type, details)
            return approved, reason

        # Check rate limit for write/execute actions
        allowed, reason = self.rate_limiter.check_action(self.agent_name)
        if not allowed:
            return False, reason

        # Check approval
        approved, reason, risk = self.check_approval(action_type, details)
        if not approved:
            return False, reason

        # Record the action
        self.record_action(cost)

        return True, "OK"

    def get_status(self) -> Dict[str, Any]:
        """Get full security status."""
        usage = self.rate_limiter.get_usage(self.agent_name)

        return {
            "agent": self.agent_name,
            "autonomy_level": self.autonomy_level.value,
            "rate_usage": usage,
            "blocked_paths_count": len(self.blocked_paths),
            "approval_required_for": list(self.require_approval),
        }

    def set_autonomy_level(self, level: str):
        """Change autonomy level at runtime."""
        self.autonomy_level = AutonomyLevel(level)

        # Update config
        config = self._load_config()
        if "autonomy" not in config:
            config["autonomy"] = {}
        config["autonomy"][self.agent_name] = level
        CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")

    def get_pending_approvals(self, action_type: str, details: Optional[Dict] = None) -> Optional[Dict]:
        """
        If an action requires approval (not blocked), return the approval request details.
        Returns None if no approval needed OR if action is blocked.
        """
        approved, reason, risk = self.check_approval(action_type, details)

        if approved:
            return None

        # Blocked actions don't get approval requests - they're just denied
        if risk == RiskLevel.BLOCKED:
            return None

        return {
            "agent": self.agent_name,
            "action_type": action_type,
            "risk_level": risk.value,
            "reason": reason,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }


def load_security_policy(agent_name: str = "agent") -> SecurityPolicy:
    """Factory function."""
    return SecurityPolicy(agent_name)


if __name__ == "__main__":
    import sys
    sys.path.insert(
        0, r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis"
    )

    print("=== Security Policy - Phase 2 ===\n")

    # Test with each autonomy level
    for level in ["read_only", "supervised", "full"]:
        print(f"--- Autonomy: {level} ---")
        policy = SecurityPolicy("opencode")
        policy.set_autonomy_level(level)

        test_actions = [
            ("file_read", {"path": "C:\\test\\file.txt"}),
            ("file_write", {"path": "C:\\test\\file.txt"}),
            ("file_delete", {"path": "C:\\test\\file.txt"}),
            ("code_execute", {"command": "python test.py"}),
            ("process_kill", {"command": "taskkill /f /pid 1234"}),
            ("vault_read", {}),
            ("memory_write", {}),
        ]

        for action, details in test_actions:
            allowed, reason = policy.can_proceed(action, details)
            status = "[OK]" if allowed else "[BLOCK]"
            print(f"  {status} {action}: {reason}")

        print()

    # Test command validation
    print("--- Command Validation ---")
    policy = SecurityPolicy("opencode")

    test_commands = [
        "python script.py",
        "git status",
        "del C:\\Windows\\system32\\cmd.exe",
        "pip install requests",
        "taskkill /f /im virus.exe",
        "powershell -encodedcommand base64stuff",
    ]

    for cmd in test_commands:
        allowed, reason = policy.validate_command(cmd)
        status = "[OK]" if allowed else "[BLOCK]"
        print(f"  {status} '{cmd}': {reason}")

    # Test rate limiting
    print("\n--- Rate Limiting ---")
    policy = SecurityPolicy("test_agent")
    for i in range(5):
        allowed, reason = policy.can_proceed("file_read", {})
        print(f"  Action {i+1}: {'OK' if allowed else reason}")

    print("\n--- Status ---")
    print(json.dumps(policy.get_status(), indent=2))
