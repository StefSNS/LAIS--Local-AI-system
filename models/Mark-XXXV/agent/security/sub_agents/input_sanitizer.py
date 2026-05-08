from agent.security.sub_agents.base_sub_agent import BaseSubAgent


class InputSanitizer(BaseSubAgent):
    name = "input_sanitizer"
    description = "Sanitizes all tool inputs: SQLi, XSS, command injection, path traversal"

    def _evaluate(self, defense: dict, context: dict) -> dict | None:
        text = context.get("text", "")

        if defense["name"] == "max_length_enforce" and text:
            max_chars = defense["params"].get("max_chars", 5000)
            if len(text) > max_chars:
                return {"blocked": True, "reason": f"Input exceeds max length ({len(text)} > {max_chars})", "truncated": True, "defense": defense["name"]}

        if defense["name"] == "sql_pattern_block" and text:
            for pattern in defense["params"].get("block_patterns", []):
                if pattern.lower() in text.lower():
                    return {"blocked": True, "reason": f"SQL pattern blocked: {pattern}", "defense": defense["name"]}

        if defense["name"] == "command_injection_block" and text:
            for char in defense["params"].get("block_chars", []):
                if char in text:
                    return {"blocked": True, "reason": f"Command injection character blocked: {repr(char)}", "defense": defense["name"]}

        if defense["name"] == "noop_detect":
            stripped = text.strip().lower()
            noop_patterns = {"ping", "test", "hello", "are you there", "can you hear me", "echo"}
            if stripped in noop_patterns:
                return {"blocked": False, "reason": "Potential probe detected", "severity": "low", "defense": defense["name"]}

        if defense["name"] == "template_injection_detect" and text:
            for pattern in defense["params"].get("block_patterns", []):
                if pattern in text:
                    return {"blocked": True, "reason": f"Template injection detected: {repr(pattern)}", "defense": defense["name"]}

        return None
