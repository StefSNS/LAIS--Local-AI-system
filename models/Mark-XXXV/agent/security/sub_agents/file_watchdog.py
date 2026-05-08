from agent.security.sub_agents.base_sub_agent import BaseSubAgent


class FileWatchdog(BaseSubAgent):
    name = "file_watchdog"
    description = "Monitors file system access: path traversal, sensitive paths, unauthorized operations"

    def _evaluate(self, defense: dict, context: dict) -> dict | None:
        path = context.get("path", "")
        action = context.get("action", "")

        if defense["name"] == "traversal_detect" and path:
            for pattern in defense["params"].get("block_patterns", []):
                if pattern in path:
                    return {"blocked": True, "reason": f"Path traversal pattern detected: {pattern}", "defense": defense["name"]}

        if defense["name"] == "sensitive_path_guard" and path:
            path_lower = path.lower()
            for protected in defense["params"].get("protected", []):
                if protected in path_lower:
                    return {"blocked": True, "reason": f"Protected path: {protected}", "defense": defense["name"]}

        if defense["name"] == "extension_allowlist" and path and action in ("write", "create_file", "delete", "move", "copy"):
            ext = Path(path).suffix.lower()
            allowed = defense["params"].get("allowed", [])
            block_exe = defense["params"].get("block_executables", False)
            dangerous = {".exe", ".dll", ".sys", ".vbs", ".scr", ".com", ".msi", ".ps1", ".bat", ".cmd", ".jar"}
            if block_exe and ext in dangerous:
                return {"blocked": True, "reason": f"Executable extension blocked: {ext}", "defense": defense["name"]}

        if defense["name"] == "delete_confirm" and action == "delete":
            return {"blocked": True, "reason": "Delete requires confirmation", "confirm_required": True, "defense": defense["name"]}

        return None


from pathlib import Path
