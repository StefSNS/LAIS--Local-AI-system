"""
Self-Improvement Loop v1.0 - Failed task analysis and auto-fix pipeline.
Tracks failures, analyzes root causes, generates improvements, tests, and deploys.
Uses decision traces as input for continuous self-optimization.
"""

import json
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable
from threading import Lock


IMPROVEMENT_LOG_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "improvements"
IMPROVEMENT_LOG_DIR.mkdir(parents=True, exist_ok=True)
IMPROVEMENT_LOG = IMPROVEMENT_LOG_DIR / "improvement_log.json"


class FailureType(str, Enum):
    WRONG_OUTPUT = "wrong_output"
    TIMEOUT = "timeout"
    FORMAT_ERROR = "format_error"
    CONTEXT_LOSS = "context_loss"
    HALLUCINATION = "hallucination"
    TOOL_FAILURE = "tool_failure"
    ROUTING_ERROR = "routing_error"


class ImprovementStatus(str, Enum):
    IDENTIFIED = "identified"
    PROPOSED = "proposed"
    TESTING = "testing"
    DEPLOYED = "deployed"
    REJECTED = "rejected"


class FailureRecord:
    """Records a task failure for analysis."""

    def __init__(
        self,
        task_description: str,
        expected_output: str,
        actual_output: str,
        failure_type: FailureType,
        agent_name: str = "",
        context: Optional[dict] = None,
    ):
        self.task_description = task_description
        self.expected_output = expected_output
        self.actual_output = actual_output
        self.failure_type = failure_type
        self.agent_name = agent_name
        self.context = context or {}
        self.timestamp = datetime.now()
        self.id = f"fail_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_description": self.task_description,
            "expected_output": self.expected_output[:500],
            "actual_output": self.actual_output[:500],
            "failure_type": self.failure_type.value,
            "agent_name": self.agent_name,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }


class Improvement:
    """A proposed or deployed improvement."""

    def __init__(
        self,
        title: str,
        description: str,
        target_area: str,
        failure_id: str = "",
        status: ImprovementStatus = ImprovementStatus.IDENTIFIED,
    ):
        self.title = title
        self.description = description
        self.target_area = target_area
        self.failure_id = failure_id
        self.status = status
        self.created_at = datetime.now()
        self.test_result: Optional[str] = None
        self.deployed_at: Optional[datetime] = None
        self.id = f"imp_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "target_area": self.target_area,
            "failure_id": self.failure_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "test_result": self.test_result,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
        }


class SelfImprovementEngine:
    """
    Continuous improvement pipeline:
    1. Detect failures (from traces or manual reports)
    2. Analyze root cause
    3. Generate improvement proposal
    4. Test improvement
    5. Deploy if successful
    """

    def __init__(self, trace_store=None, transport_chat_fn=None):
        self.trace_store = trace_store
        self.transport_chat_fn = transport_chat_fn
        self._failures = []
        self._improvements = []
        self._lock = Lock()
        self._load_log()

    def report_failure(
        self,
        task_description: str,
        expected: str,
        actual: str,
        failure_type: FailureType,
        agent_name: str = "",
        context: Optional[dict] = None,
    ) -> FailureRecord:
        """Report a task failure for analysis."""
        failure = FailureRecord(
            task_description=task_description,
            expected_output=expected,
            actual_output=actual,
            failure_type=failure_type,
            agent_name=agent_name,
            context=context,
        )
        with self._lock:
            self._failures.append(failure)
        self._save_log()
        return failure

    def analyze_failures(self, limit: int = 10) -> list[dict]:
        """Analyze recent failures and generate improvement proposals."""
        with self._lock:
            recent = self._failures[-limit:]

        if not recent:
            return []

        patterns = self._find_patterns(recent)
        proposals = []

        for pattern_type, failures in patterns.items():
            improvement = self._generate_improvement(pattern_type, failures)
            if improvement:
                proposals.append(improvement.to_dict())
                with self._lock:
                    self._improvements.append(improvement)

        self._save_log()
        return proposals

    def test_improvement(self, improvement_id: str, test_fn: Optional[Callable] = None) -> dict:
        """Test an improvement before deployment."""
        with self._lock:
            improvement = next(
                (i for i in self._improvements if i.id == improvement_id),
                None,
            )

        if not improvement:
            return {"error": "Improvement not found"}

        improvement.status = ImprovementStatus.TESTING

        if test_fn:
            try:
                result = test_fn(improvement)
                improvement.test_result = str(result)
                if result:
                    improvement.status = ImprovementStatus.DEPLOYED
                    improvement.deployed_at = datetime.now()
                    self._apply_improvement(improvement)
            except Exception as e:
                improvement.test_result = f"Test failed: {e}"
                improvement.status = ImprovementStatus.REJECTED
        else:
            improvement.status = ImprovementStatus.DEPLOYED
            improvement.deployed_at = datetime.now()
            improvement.test_result = "Auto-approved (no test function provided)"
            self._apply_improvement(improvement)

        self._save_log()
        return improvement.to_dict()

    def get_failure_stats(self) -> dict:
        with self._lock:
            if not self._failures:
                return {"total_failures": 0}

            type_counts = {}
            agent_counts = {}
            for f in self._failures:
                type_counts[f.failure_type.value] = type_counts.get(f.failure_type.value, 0) + 1
                if f.agent_name:
                    agent_counts[f.agent_name] = agent_counts.get(f.agent_name, 0) + 1

            return {
                "total_failures": len(self._failures),
                "type_breakdown": type_counts,
                "agent_breakdown": agent_counts,
                "improvements_proposed": sum(1 for i in self._improvements if i.status == ImprovementStatus.PROPOSED),
                "improvements_deployed": sum(1 for i in self._improvements if i.status == ImprovementStatus.DEPLOYED),
            }

    def get_improvement_log(self) -> list[dict]:
        return [i.to_dict() for i in self._improvements]

    def _find_patterns(self, failures: list[FailureRecord]) -> dict[str, list[FailureRecord]]:
        patterns = {}
        for f in failures:
            patterns.setdefault(f.failure_type.value, []).append(f)

        return {k: v for k, v in patterns.items() if len(v) >= 1}

    def _generate_improvement(
        self,
        pattern_type: str,
        failures: list[FailureRecord],
    ) -> Optional[Improvement]:
        if not failures:
            return None

        first = failures[0]
        titles = {
            "wrong_output": "Improve output accuracy",
            "timeout": "Optimize execution speed",
            "format_error": "Fix output formatting",
            "context_loss": "Enhance context retention",
            "hallucination": "Reduce hallucination rate",
            "tool_failure": "Improve tool reliability",
            "routing_error": "Fix task routing logic",
        }

        target_areas = {
            "wrong_output": "response_quality",
            "timeout": "performance",
            "format_error": "output_formatting",
            "context_loss": "context_management",
            "hallucination": "accuracy",
            "tool_failure": "tool_execution",
            "routing_error": "task_routing",
        }

        descriptions = []
        for f in failures:
            descriptions.append(f"Task: {f.task_description[:100]}")

        return Improvement(
            title=titles.get(pattern_type, f"Fix {pattern_type}"),
            description=f"Pattern: {pattern_type}\nAffected tasks:\n" + "\n".join(descriptions),
            target_area=target_areas.get(pattern_type, "general"),
            failure_id=first.id,
            status=ImprovementStatus.PROPOSED,
        )

    def _apply_improvement(self, improvement: Improvement) -> None:
        if improvement.target_area == "response_quality":
            self._generate_prompt_update(improvement)
        elif improvement.target_area == "output_formatting":
            self._generate_format_rules(improvement)

    def _generate_prompt_update(self, improvement: Improvement) -> None:
        if not self.transport_chat_fn:
            return

        prompt = f"""Based on this failure analysis, generate an improved system prompt instruction:

Failure pattern: {improvement.description}

Generate a clear, actionable instruction that would prevent this failure type.
Format: "ALWAYS [action] when [condition] to avoid [failure]"

Instruction:"""

        try:
            result = self.transport_chat_fn(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100,
            )
            instruction = result.get("text", "").strip()
            if instruction:
                rules_path = IMPROVEMENT_LOG_DIR / "prompt_rules.json"
                rules = []
                if rules_path.exists():
                    try:
                        rules = json.loads(rules_path.read_text(encoding="utf-8"))
                    except Exception:
                        rules = []
                rules.append({
                    "rule": instruction,
                    "source": improvement.id,
                    "created_at": datetime.now().isoformat(),
                })
                rules_path.write_text(json.dumps(rules, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _generate_format_rules(self, improvement: Improvement) -> None:
        rules_path = IMPROVEMENT_LOG_DIR / "format_rules.json"
        rules = []
        if rules_path.exists():
            try:
                rules = json.loads(rules_path.read_text(encoding="utf-8"))
            except Exception:
                rules = []
        rules.append({
            "description": improvement.description,
            "created_at": datetime.now().isoformat(),
        })
        rules_path.write_text(json.dumps(rules, indent=2), encoding="utf-8")

    def _load_log(self) -> None:
        if IMPROVEMENT_LOG.exists():
            try:
                data = json.loads(IMPROVEMENT_LOG.read_text(encoding="utf-8"))
                self._failures = data.get("failures", [])
                improvements_data = data.get("improvements", [])
                self._improvements = []
                for imp in improvements_data:
                    improvement = Improvement(
                        title=imp["title"],
                        description=imp["description"],
                        target_area=imp["target_area"],
                        failure_id=imp.get("failure_id", ""),
                        status=ImprovementStatus(imp.get("status", "identified")),
                    )
                    improvement.id = imp.get("id", improvement.id)
                    improvement.created_at = datetime.fromisoformat(imp["created_at"]) if "created_at" in imp else datetime.now()
                    improvement.test_result = imp.get("test_result")
                    if imp.get("deployed_at"):
                        improvement.deployed_at = datetime.fromisoformat(imp["deployed_at"])
                    self._improvements.append(improvement)
            except Exception:
                pass

    def _save_log(self) -> None:
        data = {
            "failures": [f.to_dict() for f in self._failures],
            "improvements": [i.to_dict() for i in self._improvements],
        }
        IMPROVEMENT_LOG.write_text(json.dumps(data, indent=2), encoding="utf-8")


_global_engine: Optional[SelfImprovementEngine] = None
_engine_lock = Lock()


def get_self_improvement_engine(
    trace_store=None,
    transport_chat_fn=None,
) -> SelfImprovementEngine:
    global _global_engine
    if _global_engine is None:
        with _engine_lock:
            if _global_engine is None:
                _global_engine = SelfImprovementEngine(trace_store, transport_chat_fn)
    return _global_engine
