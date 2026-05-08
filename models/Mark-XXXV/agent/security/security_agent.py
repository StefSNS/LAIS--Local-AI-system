import json
import random
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Callable


class ThreatLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# Lazy imports to avoid circular dependencies
_sub_agents = None


def _get_sub_agents():
    global _sub_agents
    if _sub_agents is not None:
        return _sub_agents
    from agent.security.sub_agents import (
        NetworkShield, CodeSentry, FileWatchdog, InputSanitizer,
        AuthGate, AnomalyDetector, CryptoGuard, AuditLogger, DecoyEngine,
    )
    _sub_agents = [
        NetworkShield(),
        CodeSentry(),
        FileWatchdog(),
        InputSanitizer(),
        AuthGate(),
        AnomalyDetector(),
        CryptoGuard(),
        AuditLogger(),
        DecoyEngine(),
    ]
    return _sub_agents


class SecurityAgent:
    def __init__(self):
        self._active = False
        self._lock = threading.Lock()
        self._threat_level = ThreatLevel.NONE
        self._deployed_agents: list = []
        self._attack_history: list[dict] = []
        self._defense_rotation_count = 0
        self._watch_thread: threading.Thread | None = None
        self._stop_watch = threading.Event()

    def deploy(self, threat_level: ThreatLevel = ThreatLevel.MEDIUM) -> dict:
        with self._lock:
            self._active = True
            self._threat_level = threat_level
            agents = _get_sub_agents()

            num_agents = self._agent_count_for_level(threat_level)
            selected = random.sample(agents, min(num_agents, len(agents)))

            self._deployed_agents = []
            results = []

            for agent in selected:
                defense_count = random.randint(2, 4)
                defenses = agent.activate(defense_count)
                self._deployed_agents.append(agent)
                results.append({
                    "agent": agent.name,
                    "description": agent.description,
                    "defenses": [d["name"] for d in defenses],
                    "status": "active",
                })

            self._defense_rotation_count = 0
            self._attack_history.append({
                "timestamp": time.time(),
                "event": "deploy",
                "threat_level": threat_level.name,
                "agents": len(selected),
                "total_defenses": sum(len(r["defenses"]) for r in results),
            })

            self._start_watchdog(threat_level)

            return {
                "status": "deployed",
                "threat_level": threat_level.name,
                "agents_deployed": len(selected),
                "agent_details": results,
                "message": f"Security grid active — {len(selected)} agents with randomized defenses online",
            }

    def rotate_all(self, reason: str = "attacker adaptation detected") -> dict:
        with self._lock:
            if not self._active:
                return {"status": "inactive", "message": "Security grid not deployed"}

            self._defense_rotation_count += 1
            rotations = []
            for agent in self._deployed_agents:
                new_defenses = agent.rotate_defenses(reason)
                rotations.append({
                    "agent": agent.name,
                    "new_defenses": [d["name"] for d in new_defenses],
                    "rotation": agent._rotation_count,
                })

            self._attack_history.append({
                "timestamp": time.time(),
                "event": "rotate_all",
                "reason": reason,
                "rotation_number": self._defense_rotation_count,
            })

            return {
                "status": "rotated",
                "rotation": self._defense_rotation_count,
                "reason": reason,
                "agent_rotations": rotations,
            }

    def evaluate(self, context: dict) -> dict:
        if not self._active:
            return {"status": "inactive", "message": "Security grid not deployed"}

        findings = []
        blocked = False
        alerts = []

        for agent in self._deployed_agents:
            agent_findings = agent.scan(context)
            for finding in agent_findings:
                findings.append({
                    "agent": agent.name,
                    "finding": finding,
                })
                if finding.get("blocked"):
                    blocked = True
                if finding.get("alert"):
                    alert_entry = agent.alert(finding["reason"])
                    alerts.append(alert_entry)

        return {
            "status": "blocked" if blocked else "allowed",
            "blocked": blocked,
            "findings": findings,
            "alerts": alerts,
            "findings_count": len(findings),
        }

    def assess_and_respond(self, context: dict) -> dict:
        evaluation = self.evaluate(context)

        if not self._active:
            return evaluation

        threat_score = sum(
            1 for f in evaluation["findings"]
            if f["finding"].get("blocked") or f["finding"].get("severity") in ("high", "critical")
        )

        if threat_score >= 3:
            evaluation["rotation"] = self.rotate_all("multiple high-severity threats detected")

        if evaluation.get("alerts"):
            self._attack_history.append({
                "timestamp": time.time(),
                "event": "alert_triggered",
                "alert_count": len(evaluation["alerts"]),
                "findings": len(evaluation["findings"]),
            })

        return evaluation

    def get_status(self) -> dict:
        with self._lock:
            statuses = [a.get_status() for a in self._deployed_agents] if self._active else []
            return {
                "active": self._active,
                "threat_level": self._threat_level.name if self._active else "NONE",
                "agents_deployed": len(self._deployed_agents),
                "total_defense_rotations": self._defense_rotation_count,
                "total_alerts": sum(a._alert_count for a in self._deployed_agents) if self._active else 0,
                "attack_events_logged": len(self._attack_history),
                "agents": statuses,
            }

    def disarm(self) -> dict:
        with self._lock:
            self._stop_watch.set()
            self._active = False
            for agent in self._deployed_agents:
                if hasattr(agent, "cleanup"):
                    try:
                        agent.cleanup()
                    except Exception:
                        pass
            self._deployed_agents = []
            self._attack_history.append({
                "timestamp": time.time(),
                "event": "disarm",
            })
            return {"status": "disarmed", "message": "Security grid disarmed"}

    def _agent_count_for_level(self, level: ThreatLevel) -> int:
        mapping = {
            ThreatLevel.LOW: 3,
            ThreatLevel.MEDIUM: 5,
            ThreatLevel.HIGH: 7,
            ThreatLevel.CRITICAL: 9,
        }
        return mapping.get(level, 5)

    def _start_watchdog(self, level: ThreatLevel):
        if self._watch_thread and self._watch_thread.is_alive():
            return

        self._stop_watch.clear()
        interval_map = {
            ThreatLevel.LOW: 60,
            ThreatLevel.MEDIUM: 30,
            ThreatLevel.HIGH: 15,
            ThreatLevel.CRITICAL: 5,
        }
        interval = interval_map.get(level, 30)

        def _watch_loop():
            rotation_count = 0
            while not self._stop_watch.wait(interval):
                with self._lock:
                    if not self._active:
                        break
                    rotation_count += 1
                    for agent in self._deployed_agents:
                        if rotation_count % random.randint(2, 4) == 0:
                            agent.rotate_defenses("scheduled proactive rotation")
                    if rotation_count >= 6:
                        rotation_count = 0

        self._watch_thread = threading.Thread(target=_watch_loop, daemon=True, name="SecurityWatchdog")
        self._watch_thread.start()


_security_agent = SecurityAgent()


def get_security_agent() -> SecurityAgent:
    return _security_agent
