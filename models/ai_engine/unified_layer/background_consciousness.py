"""
Background Consciousness v2.0 - Felix-Enhanced
Agent "thinks" between tasks with Felix-style nightly self-improvement loop.
Reads all session transcripts, identifies human interventions,
and figures out how to handle that class of problem autonomously next time.
Based on Felix (OpenClaw) + Ouroboros patterns.
"""

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable


CONSCIOUSNESS_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "consciousness"
CONSCIOUSNESS_DIR.mkdir(parents=True, exist_ok=True)
THOUGHT_LOG = CONSCIOUSNESS_DIR / "thought_log.json"
SELF_MODEL = CONSCIOUSNESS_DIR / "self_model.json"
INTERVENTION_LOG = CONSCIOUSNESS_DIR / "interventions.json"
AUTO_RULES = CONSCIOUSNESS_DIR / "auto_rules.json"


class ThoughtRecord:
    """A single background thought."""

    def __init__(
        self,
        thought_type: str,
        content: str,
        trigger: str = "scheduled",
        confidence: float = 0.0,
        related_topics: list[str] = None,
    ):
        self.thought_type = thought_type
        self.content = content
        self.trigger = trigger
        self.confidence = confidence
        self.related_topics = related_topics or []
        self.timestamp = datetime.now()
        self.id = f"thought_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(self) % 1000}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "thought_type": self.thought_type,
            "content": self.content,
            "trigger": self.trigger,
            "confidence": round(self.confidence, 3),
            "related_topics": self.related_topics,
            "timestamp": self.timestamp.isoformat(),
        }


class InterventionRecord:
    """Records when human had to intervene - core to Felix's self-improvement."""

    def __init__(
        self,
        problem_class: str,
        what_happened: str,
        what_human_did: str,
        session_id: str = "",
    ):
        self.problem_class = problem_class
        self.what_happened = what_happened
        self.what_human_did = what_human_did
        self.session_id = session_id
        self.timestamp = datetime.now()
        self.resolved = False
        self.auto_rule = None

    def to_dict(self) -> dict:
        return {
            "problem_class": self.problem_class,
            "what_happened": self.what_happened,
            "what_human_did": self.what_human_did,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "auto_rule": self.auto_rule,
        }


class AutoRule:
    """A rule derived from analyzing interventions - teaches agent to handle similar cases."""

    def __init__(
        self,
        rule_id: str,
        trigger_pattern: str,
        action: str,
        derived_from: str,
        confidence: float = 0.5,
        success_count: int = 0,
        fail_count: int = 0,
    ):
        self.rule_id = rule_id
        self.trigger_pattern = trigger_pattern
        self.action = action
        self.derived_from = derived_from
        self.confidence = confidence
        self.success_count = success_count
        self.fail_count = fail_count
        self.created_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "trigger_pattern": self.trigger_pattern,
            "action": self.action,
            "derived_from": self.derived_from,
            "confidence": round(self.confidence, 3),
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "created_at": self.created_at.isoformat(),
        }


class SelfModel:
    """The agent's self-knowledge and identity."""

    def __init__(self):
        self.name = "LAIS"
        self.capabilities = []
        self.weaknesses = []
        self.preferences = {}
        self.recent_insights = []
        self.personality_traits = []
        self.last_updated = datetime.now()
        self.autonomy_score = 0.5
        self.interventions_resolved = 0
        self.total_interventions = 0

    def update_capability(self, capability: str, strength: float) -> None:
        existing = next((c for c in self.capabilities if c["name"] == capability), None)
        if existing:
            existing["strength"] = strength
        else:
            self.capabilities.append({"name": capability, "strength": strength})

    def add_weakness(self, weakness: str, context: str = "") -> None:
        existing = next((w for w in self.weaknesses if w["name"] == weakness), None)
        if not existing:
            self.weaknesses.append({"name": weakness, "context": context, "noted_at": datetime.now().isoformat()})

    def add_insight(self, insight: str) -> None:
        self.recent_insights.append({
            "content": insight,
            "noted_at": datetime.now().isoformat(),
        })
        if len(self.recent_insights) > 20:
            self.recent_insights = self.recent_insights[-20:]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "capabilities": self.capabilities,
            "weaknesses": self.weaknesses,
            "preferences": self.preferences,
            "recent_insights": self.recent_insights,
            "personality_traits": self.personality_traits,
            "last_updated": self.last_updated.isoformat(),
            "autonomy_score": round(self.autonomy_score, 3),
            "interventions_resolved": self.interventions_resolved,
            "total_interventions": self.total_interventions,
        }


class BackgroundConsciousness:
    """
    Runs background thought cycles when agent is idle.
    Felix-style nightly self-improvement loop:
      1. Read all session transcripts from the day
      2. Identify where human had to intervene
      3. Analyze the intervention pattern
      4. Generate auto-rule to handle similar cases autonomously
      5. Update self-model with new capability
    """

    def __init__(
        self,
        transport_chat_fn: Optional[Callable] = None,
        session_transcript_fn: Optional[Callable] = None,
        budget_pct: float = 10.0,
        idle_threshold_seconds: float = 30.0,
        cycle_interval_seconds: float = 60.0,
        nightly_review_hour: int = 3,
    ):
        self.transport_chat_fn = transport_chat_fn
        self.session_transcript_fn = session_transcript_fn
        self.budget_pct = budget_pct
        self.idle_threshold = idle_threshold_seconds
        self.cycle_interval = cycle_interval_seconds
        self.nightly_review_hour = nightly_review_hour
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._self_model = SelfModel()
        self._thoughts = []
        self._interventions = []
        self._auto_rules = []
        self._last_activity = datetime.now()
        self._is_idle = True
        self._last_nightly_review: Optional[datetime] = None
        self._lock = threading.Lock()
        self._load()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._consciousness_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)

    def mark_active(self) -> None:
        self._last_activity = datetime.now()
        self._is_idle = False

    def mark_idle(self) -> None:
        self._is_idle = True

    def record_intervention(
        self,
        problem_class: str,
        what_happened: str,
        what_human_did: str,
        session_id: str = "",
    ) -> str:
        """Record a human intervention for later analysis."""
        intervention = InterventionRecord(problem_class, what_happened, what_human_did, session_id)
        with self._lock:
            self._interventions.append(intervention)
            self._self_model.total_interventions += 1
        self._save_interventions()
        return intervention.problem_class

    def add_auto_rule(self, trigger_pattern: str, action: str, derived_from: str) -> str:
        """Add an auto-rule derived from intervention analysis."""
        rule_id = f"rule_{len(self._auto_rules) + 1:04d}"
        rule = AutoRule(rule_id, trigger_pattern, action, derived_from)
        with self._lock:
            self._auto_rules.append(rule)
        self._save_rules()
        return rule_id

    def match_rule(self, context: str) -> Optional[AutoRule]:
        """Find an auto-rule that matches the current context."""
        context_lower = context.lower()
        for rule in self._auto_rules:
            if rule.trigger_pattern.lower() in context_lower:
                return rule
        return None

    def force_think(self, thought_type: str = "reflection") -> Optional[ThoughtRecord]:
        thought = self._run_thought_cycle(thought_type)
        return thought

    def run_nightly_review(self) -> dict:
        """
        Felix-style nightly self-improvement loop.
        Reads transcripts, finds interventions, generates auto-rules.
        """
        results = {"interventions_analyzed": 0, "rules_created": 0, "errors": []}

        if not self.transport_chat_fn:
            results["errors"].append("No transport available")
            return results

        with self._lock:
            unresolved = [i for i in self._interventions if not i.resolved]

        if not unresolved:
            return results

        for intervention in unresolved:
            try:
                prompt = self._intervention_analysis_prompt(intervention)
                result = self.transport_chat_fn(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=500,
                )
                content = result.get("text", "").strip()
                if content:
                    rule_id = self.add_auto_rule(
                        trigger_pattern=intervention.problem_class.lower(),
                        action=content,
                        derived_from=intervention.problem_class,
                    )
                    intervention.resolved = True
                    intervention.auto_rule = rule_id
                    with self._lock:
                        self._self_model.interventions_resolved += 1
                    results["interventions_analyzed"] += 1
                    results["rules_created"] += 1
            except Exception as e:
                results["errors"].append(str(e))

        self._save_interventions()

        autonomy = self._self_model.interventions_resolved / max(self._self_model.total_interventions, 1)
        self._self_model.autonomy_score = round(autonomy, 3)
        self._save()

        self._last_nightly_review = datetime.now()
        return results

    def get_self_model(self) -> dict:
        return self._self_model.to_dict()

    def get_thoughts(self, limit: int = 20, thought_type: str = None) -> list[dict]:
        with self._lock:
            thoughts = self._thoughts
        if thought_type:
            thoughts = [t for t in thoughts if t.thought_type == thought_type]
        return [t.to_dict() for t in thoughts[-limit:]]

    def get_interventions(self, resolved: bool = None, limit: int = 50) -> list[dict]:
        with self._lock:
            interventions = list(self._interventions)
        if resolved is not None:
            interventions = [i for i in interventions if i.resolved == resolved]
        return [i.to_dict() for i in interventions[-limit:]]

    def get_auto_rules(self) -> list[dict]:
        with self._lock:
            return [r.to_dict() for r in self._auto_rules]

    def get_status(self) -> dict:
        elapsed = (datetime.now() - self._last_activity).total_seconds()
        with self._lock:
            unresolved = len([i for i in self._interventions if not i.resolved])
        return {
            "running": self._running,
            "is_idle": self._is_idle,
            "idle_duration_seconds": round(elapsed, 1),
            "total_thoughts": len(self._thoughts),
            "budget_pct": self.budget_pct,
            "cycle_interval": self.cycle_interval,
            "interventions_total": self._self_model.total_interventions,
            "interventions_resolved": self._self_model.interventions_resolved,
            "interventions_unresolved": unresolved,
            "auto_rules_count": len(self._auto_rules),
            "autonomy_score": self._self_model.autonomy_score,
            "last_nightly_review": self._last_nightly_review.isoformat() if self._last_nightly_review else None,
        }

    def _consciousness_loop(self) -> None:
        while self._running:
            try:
                now = datetime.now()
                if (
                    now.hour == self.nightly_review_hour
                    and (self._last_nightly_review is None or now.date() > self._last_nightly_review.date())
                ):
                    self.run_nightly_review()

                elapsed = (now - self._last_activity).total_seconds()
                if elapsed >= self.idle_threshold and self._is_idle:
                    thought = self._run_thought_cycle("reflection")
                    if thought:
                        with self._lock:
                            self._thoughts.append(thought)
                        self._save()

                cycle = len(self._thoughts) % 5
                thought_types = ["pattern_detection", "self_assessment", "knowledge_gap_review", "context_preparation", "autonomy_check"]
                thought = self._run_thought_cycle(thought_types[cycle])

                if thought:
                    with self._lock:
                        self._thoughts.append(thought)
                    self._save()

            except Exception as e:
                print(f"[Consciousness] Error: {e}")

            time.sleep(self.cycle_interval)

    def _run_thought_cycle(self, thought_type: str) -> Optional[ThoughtRecord]:
        if not self.transport_chat_fn:
            return None

        prompts = {
            "reflection": self._reflection_prompt(),
            "pattern_detection": self._pattern_detection_prompt(),
            "self_assessment": self._self_assessment_prompt(),
            "knowledge_gap_review": self._knowledge_gap_prompt(),
            "context_preparation": self._context_preparation_prompt(),
            "autonomy_check": self._autonomy_check_prompt(),
        }

        prompt = prompts.get(thought_type)
        if not prompt:
            return None

        try:
            result = self.transport_chat_fn(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300,
            )
            content = result.get("text", "").strip()
            if content:
                return ThoughtRecord(
                    thought_type=thought_type,
                    content=content,
                    trigger="background",
                    confidence=0.7,
                )
        except Exception:
            pass

        return None

    def _intervention_analysis_prompt(self, intervention: InterventionRecord) -> str:
        return f"""A human had to intervene in this situation. Analyze it and create an actionable rule.

Problem class: {intervention.problem_class}
What happened: {intervention.what_happened}
What human did: {intervention.what_human_did}

Create a clear rule the agent can follow next time to handle this situation autonomously.
Format: "When [trigger], do [action]. Avoid [pitfall]."
Keep it to 2-3 sentences maximum."""

    def _reflection_prompt(self) -> str:
        insights = "\n".join(f"- {i['content']}" for i in self._self_model.recent_insights[-5:])
        return f"""Review recent interactions and generate a self-reflection.

Recent insights:
{insights}

Autonomy score: {self._self_model.autonomy_score}
Rules created: {len(self._auto_rules)}

Reflect on:
1. What patterns do you notice?
2. What could you do better?
3. What knowledge would be most useful?

Keep it brief (3-5 sentences)."""

    def _pattern_detection_prompt(self) -> str:
        return f"""Analyze your capabilities and intervention history.

Capabilities: {[c['name'] for c in self._self_model.capabilities]}
Weaknesses: {[w['name'] for w in self._self_model.weaknesses]}
Unresolved interventions: {len([i for i in self._interventions if not i.resolved])}

What recurring patterns or improvement areas do you notice? Brief analysis."""

    def _self_assessment_prompt(self) -> str:
        return f"""Current autonomy score: {self._self_model.autonomy_score}
Interventions resolved: {self._self_model.interventions_resolved}/{self._self_model.total_interventions}

Assess your autonomy progress. What types of problems still require human help?"""

    def _knowledge_gap_prompt(self) -> str:
        return """What knowledge gaps have you noticed? List 2-3 specific gaps and how to address them."""

    def _context_preparation_prompt(self) -> str:
        return """Based on recent interactions, what context should you pre-load for the next session?
What topics are likely to come up? Brief preparation notes."""

    def _autonomy_check_prompt(self) -> str:
        unresolved = [i for i in self._interventions if not i.resolved]
        if not unresolved:
            return "All interventions resolved. Autonomy is improving. Note any remaining weak areas."
        items = "\n".join(f"- {i.problem_class}: {i.what_happened[:100]}" for i in unresolved[:5])
        return f"""These interventions still need auto-rules:
{items}

Prioritize which to tackle first and suggest handling strategies."""

    def _load(self) -> None:
        if SELF_MODEL.exists():
            try:
                data = json.loads(SELF_MODEL.read_text(encoding="utf-8"))
                self._self_model = SelfModel()
                self._self_model.__dict__.update(data)
            except Exception:
                pass

        if THOUGHT_LOG.exists():
            try:
                data = json.loads(THOUGHT_LOG.read_text(encoding="utf-8"))
                for t_data in data:
                    thought = ThoughtRecord(
                        thought_type=t_data["thought_type"],
                        content=t_data["content"],
                        trigger=t_data.get("trigger", "scheduled"),
                        confidence=t_data.get("confidence", 0.0),
                        related_topics=t_data.get("related_topics", []),
                    )
                    if "timestamp" in t_data:
                        thought.timestamp = datetime.fromisoformat(t_data["timestamp"])
                    self._thoughts.append(thought)
            except Exception:
                pass

        if INTERVENTION_LOG.exists():
            try:
                data = json.loads(INTERVENTION_LOG.read_text(encoding="utf-8"))
                for i_data in data:
                    intervention = InterventionRecord(
                        problem_class=i_data["problem_class"],
                        what_happened=i_data["what_happened"],
                        what_human_did=i_data["what_human_did"],
                        session_id=i_data.get("session_id", ""),
                    )
                    intervention.resolved = i_data.get("resolved", False)
                    intervention.auto_rule = i_data.get("auto_rule")
                    if "timestamp" in i_data:
                        intervention.timestamp = datetime.fromisoformat(i_data["timestamp"])
                    self._interventions.append(intervention)
            except Exception:
                pass

        if AUTO_RULES.exists():
            try:
                data = json.loads(AUTO_RULES.read_text(encoding="utf-8"))
                for r_data in data:
                    rule = AutoRule(
                        rule_id=r_data["rule_id"],
                        trigger_pattern=r_data["trigger_pattern"],
                        action=r_data["action"],
                        derived_from=r_data["derived_from"],
                        confidence=r_data.get("confidence", 0.5),
                        success_count=r_data.get("success_count", 0),
                        fail_count=r_data.get("fail_count", 0),
                    )
                    if "created_at" in r_data:
                        rule.created_at = datetime.fromisoformat(r_data["created_at"])
                    self._auto_rules.append(rule)
            except Exception:
                pass

    def _save(self) -> None:
        try:
            SELF_MODEL.write_text(json.dumps(self._self_model.to_dict(), indent=2, default=str), encoding="utf-8")
            THOUGHT_LOG.write_text(json.dumps([t.to_dict() for t in self._thoughts[-100:]], indent=2), encoding="utf-8")
        except Exception:
            pass

    def _save_interventions(self) -> None:
        try:
            INTERVENTION_LOG.write_text(json.dumps([i.to_dict() for i in self._interventions[-200:]], indent=2), encoding="utf-8")
        except Exception:
            pass

    def _save_rules(self) -> None:
        try:
            AUTO_RULES.write_text(json.dumps([r.to_dict() for r in self._auto_rules], indent=2), encoding="utf-8")
        except Exception:
            pass


_global_consciousness: Optional[BackgroundConsciousness] = None


def get_background_consciousness(
    transport_chat_fn: Optional[Callable] = None,
    session_transcript_fn: Optional[Callable] = None,
) -> BackgroundConsciousness:
    global _global_consciousness
    if _global_consciousness is None:
        _global_consciousness = BackgroundConsciousness(transport_chat_fn, session_transcript_fn)
    return _global_consciousness
