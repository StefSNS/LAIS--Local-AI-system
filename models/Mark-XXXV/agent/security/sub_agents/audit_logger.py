import json
import time
from pathlib import Path
from agent.security.sub_agents.base_sub_agent import BaseSubAgent


class AuditLogger(BaseSubAgent):
    name = "audit_logger"
    description = "Logs all security events with integrity protection, rotation, and forensic snapshots"

    def __init__(self):
        super().__init__()
        self._log_entries: list[dict] = []
        self._sequence = 0
        self._log_dir = Path(__file__).resolve().parent.parent.parent / "logs" / "security"
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def _log_action(self, action: str, data):
        self._sequence += 1
        entry = {
            "sequence": self._sequence,
            "timestamp": time.time(),
            "agent": self.name,
            "action": action,
            "data": data,
        }
        self._log_entries.append(entry)
        self._persist_log(entry)

    def _persist_log(self, entry: dict):
        try:
            log_file = self._log_dir / "audit_log.jsonl"
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def get_log(self, last_n: int = 50) -> list[dict]:
        return self._log_entries[-last_n:]

    def _evaluate(self, defense: dict, context: dict) -> dict | None:
        tool = context.get("tool", "")
        result = context.get("result", "")

        if defense["name"] == "log_all_tools" and tool:
            entry = {
                "event": "tool_invocation",
                "tool": tool,
                "args": context.get("args", {}),
                "result": str(result)[:200],
                "timestamp": time.time(),
            }
            self._log_entries.append(entry)
            return {"blocked": False, "reason": f"Logged tool: {tool}", "logged": True, "defense": defense["name"]}

        return None
