"""
Cross-Session Learning v1.0
Agent remembers patterns across sessions without explicit search.
Embedding-based memory + pattern detection for persistent learning.
Detects recurring issues, preferences, and knowledge gaps.
"""

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from threading import Lock


LEARNING_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "cross_session"
LEARNING_DIR.mkdir(parents=True, exist_ok=True)
LEARNING_DB = LEARNING_DIR / "learning_db.json"
PATTERN_DB = LEARNING_DIR / "pattern_db.json"


class SessionProfile:
    """Captures the essence of a single session."""

    def __init__(
        self,
        session_id: str,
        topics: list[str],
        tasks_completed: int,
        tasks_failed: int,
        tools_used: list[str],
        duration_minutes: float,
        sentiment: str = "neutral",
    ):
        self.session_id = session_id
        self.topics = topics
        self.tasks_completed = tasks_completed
        self.tasks_failed = tasks_failed
        self.tools_used = tools_used
        self.duration_minutes = duration_minutes
        self.sentiment = sentiment
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "topics": self.topics,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tools_used": self.tools_used,
            "duration_minutes": self.duration_minutes,
            "sentiment": self.sentiment,
            "timestamp": self.timestamp.isoformat(),
        }


class Pattern:
    """A detected recurring pattern across sessions."""

    def __init__(
        self,
        pattern_type: str,
        description: str,
        frequency: int,
        confidence: float,
        related_topics: list[str],
    ):
        self.pattern_type = pattern_type
        self.description = description
        self.frequency = frequency
        self.confidence = confidence
        self.related_topics = related_topics
        self.first_seen = datetime.now()
        self.last_seen = datetime.now()

    def to_dict(self) -> dict:
        return {
            "pattern_type": self.pattern_type,
            "description": self.description,
            "frequency": self.frequency,
            "confidence": round(self.confidence, 3),
            "related_topics": self.related_topics,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
        }


class KnowledgeGap:
    """Identified area where the agent lacks knowledge."""

    def __init__(
        self,
        topic: str,
        failure_count: int,
        last_encountered: datetime,
        suggestions: list[str] = None,
    ):
        self.topic = topic
        self.failure_count = failure_count
        self.last_encountered = last_encountered
        self.suggestions = suggestions or []

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "failure_count": self.failure_count,
            "last_encountered": self.last_encountered.isoformat(),
            "suggestions": self.suggestions,
        }


class UserPreference:
    """Learned user preference."""

    def __init__(
        self,
        preference_type: str,
        value: str,
        confidence: float,
        evidence_count: int,
    ):
        self.preference_type = preference_type
        self.value = value
        self.confidence = confidence
        self.evidence_count = evidence_count

    def to_dict(self) -> dict:
        return {
            "preference_type": self.preference_type,
            "value": self.value,
            "confidence": round(self.confidence, 3),
            "evidence_count": self.evidence_count,
        }


class CrossSessionLearner:
    """
    Learns across sessions:
    1. Track session profiles
    2. Detect recurring patterns (topics, failures, preferences)
    3. Identify knowledge gaps
    4. Generate personalized context for new sessions
    """

    def __init__(self):
        self._profiles = []
        self._patterns = []
        self._gaps = {}
        self._preferences = {}
        self._topic_vectors = defaultdict(list)
        self._lock = Lock()
        self._load()

    def record_session(self, profile: SessionProfile) -> None:
        """Record a completed session."""
        with self._lock:
            self._profiles.append(profile)
            for topic in profile.topics:
                self._topic_vectors[topic].append(profile.session_id)
        self._save()

    def record_task(
        self,
        session_id: str,
        task_description: str,
        success: bool,
        topic: str = "",
    ) -> None:
        """Record individual task outcome for pattern detection."""
        if not success:
            self._track_failure(task_description, topic)
        self._detect_patterns()

    def get_session_context(self, current_topics: list[str]) -> dict:
        """Generate personalized context for a new session."""
        context = {
            "relevant_past_sessions": [],
            "known_preferences": [],
            "knowledge_warnings": [],
            "suggested_resources": [],
        }

        for profile in self._profiles[-10:]:
            overlap = set(profile.topics) & set(current_topics)
            if overlap:
                context["relevant_past_sessions"].append({
                    "session_id": profile.session_id,
                    "topics": profile.topics,
                    "success_rate": self._success_rate(profile),
                })

        for pref in self._preferences.values():
            if pref.confidence > 0.7:
                context["known_preferences"].append(pref.to_dict())

        for topic in current_topics:
            if topic in self._gaps:
                gap = self._gaps[topic]
                context["knowledge_warnings"].append(gap.to_dict())

        return context

    def detect_patterns(self) -> list[dict]:
        """Run pattern detection across all sessions."""
        self._detect_patterns()
        return [p.to_dict() for p in self._patterns]

    def get_knowledge_gaps(self) -> list[dict]:
        return [g.to_dict() for g in self._gaps.values()]

    def get_preferences(self) -> list[dict]:
        return [p.to_dict() for p in self._preferences.values()]

    def get_stats(self) -> dict:
        return {
            "total_sessions": len(self._profiles),
            "total_patterns": len(self._patterns),
            "knowledge_gaps": len(self._gaps),
            "preferences_learned": len(self._preferences),
            "unique_topics": len(self._topic_vectors),
            "most_common_topics": self._top_topics(5),
        }

    def _success_rate(self, profile: SessionProfile) -> float:
        total = profile.tasks_completed + profile.tasks_failed
        if total == 0:
            return 0.0
        return round(profile.tasks_completed / total, 2)

    def _track_failure(self, task_description: str, topic: str) -> None:
        if not topic:
            topic = self._extract_topic(task_description)

        if topic not in self._gaps:
            self._gaps[topic] = KnowledgeGap(
                topic=topic,
                failure_count=1,
                last_encountered=datetime.now(),
                suggestions=self._generate_suggestions(topic),
            )
        else:
            self._gaps[topic].failure_count += 1
            self._gaps[topic].last_encountered = datetime.now()

    def _detect_patterns(self) -> None:
        if len(self._profiles) < 3:
            return

        topic_freq = Counter()
        tool_freq = Counter()
        failure_topics = Counter()

        for profile in self._profiles:
            for topic in profile.topics:
                topic_freq[topic] += 1
            for tool in profile.tools_used:
                tool_freq[tool] += 1
            if profile.tasks_failed > profile.tasks_completed:
                for topic in profile.topics:
                    failure_topics[topic] += 1

        new_patterns = []

        for topic, count in topic_freq.items():
            if count >= 3:
                new_patterns.append(Pattern(
                    pattern_type="frequent_topic",
                    description=f"Topic '{topic}' appears in {count} sessions",
                    frequency=count,
                    confidence=min(1.0, count / 10),
                    related_topics=[],
                ))

        for tool, count in tool_freq.items():
            if count >= 4:
                new_patterns.append(Pattern(
                    pattern_type="preferred_tool",
                    description=f"Tool '{tool}' used in {count} sessions",
                    frequency=count,
                    confidence=min(1.0, count / 8),
                    related_topics=[],
                ))

        for topic, count in failure_topics.items():
            if count >= 2:
                new_patterns.append(Pattern(
                    pattern_type="recurring_failure",
                    description=f"Struggles with '{topic}' in {count} sessions",
                    frequency=count,
                    confidence=min(1.0, count / 5),
                    related_topics=[topic],
                ))

        with self._lock:
            self._patterns = new_patterns

    def _extract_topic(self, text: str) -> str:
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        stop_words = {"this", "that", "with", "from", "have", "been", "will", "would"}
        meaningful = [w for w in words if w not in stop_words]
        return meaningful[0] if meaningful else "general"

    def _generate_suggestions(self, topic: str) -> list[str]:
        suggestions = {
            "code": ["Review Python documentation", "Practice with coding exercises"],
            "database": ["Study SQL fundamentals", "Learn about indexing strategies"],
            "api": ["Review REST API best practices", "Study authentication patterns"],
            "security": ["Learn OWASP Top 10", "Study encryption fundamentals"],
            "deploy": ["Learn Docker basics", "Study CI/CD pipeline design"],
        }
        return suggestions.get(topic, [f"Research '{topic}' fundamentals"])

    def _top_topics(self, n: int) -> list[str]:
        topic_counts = Counter()
        for profile in self._profiles:
            for topic in profile.topics:
                topic_counts[topic] += 1
        return [topic for topic, _ in topic_counts.most_common(n)]

    def _save(self) -> None:
        data = {
            "profiles": [p.to_dict() for p in self._profiles],
            "patterns": [p.to_dict() for p in self._patterns],
            "gaps": {k: v.to_dict() for k, v in self._gaps.items()},
            "preferences": {k: v.to_dict() for k, v in self._preferences.items()},
            "topic_vectors": dict(self._topic_vectors),
        }
        LEARNING_DB.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self) -> None:
        if not LEARNING_DB.exists():
            return
        try:
            data = json.loads(LEARNING_DB.read_text(encoding="utf-8"))
            self._profiles = []
            for p in data.get("profiles", []):
                profile = SessionProfile(
                    session_id=p["session_id"],
                    topics=p["topics"],
                    tasks_completed=p["tasks_completed"],
                    tasks_failed=p["tasks_failed"],
                    tools_used=p["tools_used"],
                    duration_minutes=p["duration_minutes"],
                    sentiment=p.get("sentiment", "neutral"),
                )
                profile.timestamp = datetime.fromisoformat(p["timestamp"]) if "timestamp" in p else datetime.now()
                self._profiles.append(profile)

            self._patterns = []
            for p in data.get("patterns", []):
                pattern = Pattern(
                    pattern_type=p["pattern_type"],
                    description=p["description"],
                    frequency=p["frequency"],
                    confidence=p["confidence"],
                    related_topics=p.get("related_topics", []),
                )
                pattern.first_seen = datetime.fromisoformat(p["first_seen"]) if "first_seen" in p else datetime.now()
                pattern.last_seen = datetime.fromisoformat(p["last_seen"]) if "last_seen" in p else datetime.now()
                self._patterns.append(pattern)

            self._gaps = {}
            for k, v in data.get("gaps", {}).items():
                self._gaps[k] = KnowledgeGap(
                    topic=v["topic"],
                    failure_count=v["failure_count"],
                    last_encountered=datetime.fromisoformat(v["last_encountered"]),
                    suggestions=v.get("suggestions", []),
                )

            self._topic_vectors = defaultdict(list, data.get("topic_vectors", {}))
        except Exception:
            pass


_global_learner: Optional[CrossSessionLearner] = None
_learner_lock = Lock()


def get_cross_session_learner() -> CrossSessionLearner:
    global _global_learner
    if _global_learner is None:
        with _learner_lock:
            if _global_learner is None:
                _global_learner = CrossSessionLearner()
    return _global_learner
