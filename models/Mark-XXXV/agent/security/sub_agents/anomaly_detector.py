import time
from collections import defaultdict
from agent.security.sub_agents.base_sub_agent import BaseSubAgent


class AnomalyDetector(BaseSubAgent):
    name = "anomaly_detector"
    description = "Detects behavioral anomalies: unusual patterns, escalation chains, reconnaissance"

    def __init__(self):
        super().__init__()
        self._tool_history: list[tuple[float, str]] = []
        self._input_history: list[str] = []

    def _evaluate(self, defense: dict, context: dict) -> dict | None:
        tool = context.get("tool", "")
        now = time.time()

        if defense["name"] == "frequency_analysis" and tool:
            window = defense["params"].get("window_minutes", 5) * 60
            threshold = defense["params"].get("threshold", 50)
            self._tool_history.append((now, tool))
            recent = [t for t in self._tool_history if now - t[0] < window]
            if len(recent) > threshold:
                return {"blocked": True, "reason": f"Tool frequency spike: {len(recent)} calls in {window//60}min", "defense": defense["name"]}

        if defense["name"] == "time_anomaly":
            unusual_hours = defense["params"].get("unusual_hours", [0, 6])
            current_hour = time.localtime().tm_hour
            if unusual_hours[0] <= current_hour <= unusual_hours[1]:
                return {"blocked": False, "reason": f"Activity during unusual hours ({current_hour}:00)", "severity": "medium", "defense": defense["name"]}

        if defense["name"] == "escalation_detect" and tool:
            chains = defense["params"].get("block_chain", [])
            for chain in chains:
                steps = [s.strip() for s in chain.split("->")]
                self._tool_history.append((now, tool))
                recent_tools = [t[1] for t in self._tool_history if now - t[0] < 30]
                if len(recent_tools) >= len(steps):
                    window_tools = recent_tools[-len(steps):]
                    if window_tools == steps:
                        return {"blocked": True, "reason": f"Escalation chain detected: {'->'.join(steps)}", "defense": defense["name"]}

        if defense["name"] == "repetition_detect":
            text = context.get("text", "")
            max_identical = defense["params"].get("max_identical", 3)
            window_sec = defense["params"].get("window_seconds", 60)
            if text:
                self._input_history.append(text)
                recent = [t for t in self._input_history if now - time.time() < window_sec]
                same_count = sum(1 for t in recent if t == text)
                if same_count > max_identical:
                    return {"blocked": True, "reason": f"Repetitive input detected ({same_count}x same text)", "defense": defense["name"]}

        return None
