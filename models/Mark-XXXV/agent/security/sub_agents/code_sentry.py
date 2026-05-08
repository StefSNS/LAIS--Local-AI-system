from agent.security.sub_agents.base_sub_agent import BaseSubAgent


class CodeSentry(BaseSubAgent):
    name = "code_sentry"
    description = "Monitors and validates code execution: RCE, eval abuse, unsafe imports"

    def _evaluate(self, defense: dict, context: dict) -> dict | None:
        code = context.get("code", "")
        patterns = defense.get("params", {}).get("patterns", [])

        if defense["name"] == "code_pattern_block" and code:
            for pattern in patterns:
                if pattern in code:
                    return {
                        "blocked": True,
                        "reason": f"Code contains blocked pattern: {pattern}",
                        "defense": defense["name"],
                    }

        if defense["name"] == "timeout_enforce":
            requested_timeout = context.get("timeout", 0)
            max_s = defense["params"].get("max_s", 120)
            if requested_timeout > max_s or requested_timeout == 0:
                return {
                    "blocked": False,
                    "reason": f"Enforcing max timeout: {max_s}s",
                    "enforced_timeout": max_s,
                    "defense": defense["name"],
                }

        return None
