import time
from agent.security.sub_agents.base_sub_agent import BaseSubAgent


class AuthGate(BaseSubAgent):
    name = "auth_gate"
    description = "Manages authentication, rate limiting, token security, and credential protection"

    def __init__(self):
        super().__init__()
        self._attempt_history: list[float] = []
        self._lockout_until: float = 0.0

    def _evaluate(self, defense: dict, context: dict) -> dict | None:
        if defense["name"] == "rate_limit":
            max_attempts = defense["params"].get("max_attempts_per_min", 5)
            lockout_min = defense["params"].get("lockout_minutes", 15)
            now = time.time()

            if now < self._lockout_until:
                remaining = int(self._lockout_until - now)
                return {"blocked": True, "reason": f"Rate limited — lockout active for {remaining}s more", "defense": defense["name"]}

            self._attempt_history = [t for t in self._attempt_history if now - t < 60]
            self._attempt_history.append(now)
            if len(self._attempt_history) > max_attempts:
                self._lockout_until = now + (lockout_min * 60)
                return {"blocked": True, "reason": f"Rate limit exceeded — locked out for {lockout_min} min", "defense": defense["name"]}

        if defense["name"] == "key_rotation_warn":
            key_age = context.get("key_age_days", 0)
            max_age = defense["params"].get("max_age_days", 30)
            warn_days = defense["params"].get("warn_days", 7)
            if key_age >= max_age:
                return {"blocked": False, "reason": f"API key expired ({key_age}d > {max_age}d) — rotation required", "severity": "critical", "defense": defense["name"]}
            if key_age >= max_age - warn_days:
                return {"blocked": False, "reason": f"API key expiring soon ({key_age}d/{max_age}d)", "severity": "warning", "defense": defense["name"]}

        if defense["name"] == "jitter_delay":
            import random
            delay_ms = random.randint(
                defense["params"].get("min_ms", 100),
                defense["params"].get("max_ms", 500),
            )
            return {"blocked": False, "reason": f"Applied jitter delay: {delay_ms}ms", "delay_ms": delay_ms, "defense": defense["name"]}

        return None
