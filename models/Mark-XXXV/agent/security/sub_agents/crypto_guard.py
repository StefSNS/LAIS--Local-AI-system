from agent.security.sub_agents.base_sub_agent import BaseSubAgent


class CryptoGuard(BaseSubAgent):
    name = "crypto_guard"
    description = "Manages encryption, key protection, secret redaction, and cryptographic hygiene"

    def _evaluate(self, defense: dict, context: dict) -> dict | None:
        text = context.get("text", "")
        log_entry = context.get("log_entry", "")

        if defense["name"] == "secret_redact_logs" and log_entry:
            redacted = log_entry
            for pattern in defense["params"].get("redact_patterns", []):
                if pattern in redacted:
                    redacted = redacted.replace(pattern, "***REDACTED***")
            if redacted != log_entry:
                return {"blocked": False, "reason": "Secrets redacted from log output", "redacted": redacted, "defense": defense["name"]}

        if defense["name"] == "key_validate":
            key = context.get("api_key", "")
            if key:
                prefixes = {"AIza": "Gemini", "sk-": "OpenAI", "ghp_": "GitHub PAT", "gho_": "GitHub OAuth"}
                for prefix, service in prefixes.items():
                    if key.startswith(prefix):
                        if len(key) < 20:
                            return {"blocked": False, "reason": f"{service} key appears truncated/invalid", "severity": "warning", "defense": defense["name"]}
                        break
                if len(key) > 200:
                    return {"blocked": False, "reason": "Key length unusual — possible injection", "severity": "medium", "defense": defense["name"]}

        return None
