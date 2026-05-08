import json
import random
import time
from pathlib import Path
from typing import Any


DEFENSE_PROFILES_PATH = Path(__file__).resolve().parent.parent / "defense_profiles.json"


class BaseSubAgent:
    name: str = "base"
    description: str = "Base security sub-agent"

    def __init__(self):
        self._active_defenses: list[dict] = []
        self._available_defenses: list[dict] = []
        self._rotation_count = 0
        self._defense_history: list[dict] = []
        self._alert_count = 0
        self._last_rotation_time = 0.0
        self._load_defenses()

    def _load_defenses(self):
        try:
            with open(DEFENSE_PROFILES_PATH) as f:
                profiles = json.load(f)
            key = self.__class__.__name__
            snake_key = _to_snake(key)
            profile = profiles.get(snake_key, profiles.get(key, []))
            if isinstance(profile, dict):
                self._available_defenses = profile.get("defenses", [])
            else:
                self._available_defenses = profile
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            self._available_defenses = []

    def activate(self, count: int = 3) -> list[dict]:
        self._active_defenses = self._pick_random(count)
        self._rotation_count = 0
        self._alert_count = 0
        self._log_action("activated", self._active_defenses)
        return self._active_defenses

    def rotate_defenses(self, reason: str = "attacker adapted") -> list[dict]:
        self._defense_history.append({
            "timestamp": time.time(),
            "rotation": self._rotation_count,
            "defenses": list(self._active_defenses),
            "reason": reason,
        })
        self._rotation_count += 1
        new_count = random.randint(2, min(5, len(self._available_defenses)))
        self._active_defenses = self._pick_random(new_count)
        self._log_action("rotated", self._active_defenses)
        return self._active_defenses

    def get_status(self) -> dict:
        return {
            "agent": self.name,
            "active_defenses": len(self._active_defenses),
            "rotation_count": self._rotation_count,
            "alert_count": self._alert_count,
            "defenses": [d["name"] for d in self._active_defenses],
        }

    def alert(self, message: str) -> dict:
        self._alert_count += 1
        alert_entry = {
            "agent": self.name,
            "alert": self._alert_count,
            "message": message,
            "timestamp": time.time(),
            "active_defenses": [d["name"] for d in self._active_defenses],
        }
        self._log_action("alert", alert_entry)
        return alert_entry

    def scan(self, context: dict) -> list[dict]:
        findings = []
        for defense in self._active_defenses:
            finding = self._evaluate(defense, context)
            if finding:
                findings.append(finding)
        return findings

    def _evaluate(self, defense: dict, context: dict) -> dict | None:
        return None

    def _pick_random(self, count: int) -> list[dict]:
        if not self._available_defenses:
            return []
        k = min(count, len(self._available_defenses))
        chosen = random.sample(self._available_defenses, k)
        for c in chosen:
            c = dict(c)
            c["activated_at"] = time.time()
        return chosen

    def _log_action(self, action: str, data: Any):
        pass


def _to_snake(name: str) -> str:
    return "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip("_")
