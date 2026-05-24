"""
Observability / LLMOps v1.0
Metrics tracking for prompts, models, agents, costs, latency, and quality.
Based on Dify LLMOps, Langfuse, and Arize Phoenix patterns.
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


OBS_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "observability"
OBS_DIR.mkdir(parents=True, exist_ok=True)
METRICS_FILE = OBS_DIR / "metrics.json"
TRACES_FILE = OBS_DIR / "traces.json"


class Trace:
    """A single LLM interaction trace."""

    def __init__(
        self,
        trace_id: str,
        span_type: str,
        model: str = "",
        prompt: str = "",
        response: str = "",
        tokens_in: int = 0,
        tokens_out: int = 0,
        latency_ms: float = 0.0,
        cost: float = 0.0,
        agent: str = "",
        session_id: str = "",
        tags: list[str] = None,
        quality_score: float = 0.0,
        error: str = "",
    ):
        self.trace_id = trace_id
        self.span_type = span_type
        self.model = model
        self.prompt = prompt
        self.response = response
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.latency_ms = latency_ms
        self.cost = cost
        self.agent = agent
        self.session_id = session_id
        self.tags = tags or []
        self.quality_score = quality_score
        self.error = error
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "span_type": self.span_type,
            "model": self.model,
            "prompt_preview": self.prompt[:200] if self.prompt else "",
            "response_preview": self.response[:200] if self.response else "",
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "total_tokens": self.tokens_in + self.tokens_out,
            "latency_ms": round(self.latency_ms, 1),
            "cost": round(self.cost, 6),
            "agent": self.agent,
            "session_id": self.session_id,
            "tags": self.tags,
            "quality_score": round(self.quality_score, 3),
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class ObservabilityEngine:
    """
    LLMOps observability engine.
    Tracks: traces, costs, latency, token usage, quality scores, errors.
    """

    def __init__(self):
        self._traces = []
        self._max_traces = 5000
        self._load()

    def trace(
        self,
        span_type: str,
        model: str = "",
        prompt: str = "",
        response: str = "",
        tokens_in: int = 0,
        tokens_out: int = 0,
        latency_ms: float = 0.0,
        cost: float = 0.0,
        agent: str = "",
        session_id: str = "",
        tags: list[str] = None,
        quality_score: float = 0.0,
        error: str = "",
    ) -> str:
        trace_id = str(uuid.uuid4())[:12]
        trace = Trace(
            trace_id=trace_id,
            span_type=span_type,
            model=model,
            prompt=prompt,
            response=response,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            cost=cost,
            agent=agent,
            session_id=session_id,
            tags=tags,
            quality_score=quality_score,
            error=error,
        )
        self._traces.append(trace)
        if len(self._traces) > self._max_traces:
            self._traces = self._traces[-self._max_traces:]
        self._save_traces()
        return trace_id

    def trace_call(self, fn, model: str = "", agent: str = "", session_id: str = "", tags: list[str] = None):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = fn(*args, **kwargs)
                latency_ms = (time.time() - start) * 1000
                prompt = str(args[0]) if args else str(kwargs)
                response = str(result.get("text", "")) if isinstance(result, dict) else str(result)
                self.trace(
                    span_type="llm_call",
                    model=model,
                    prompt=prompt,
                    response=response,
                    latency_ms=latency_ms,
                    agent=agent,
                    session_id=session_id,
                    tags=tags,
                )
                return result
            except Exception as e:
                latency_ms = (time.time() - start) * 1000
                self.trace(
                    span_type="llm_call",
                    model=model,
                    error=str(e),
                    latency_ms=latency_ms,
                    agent=agent,
                    session_id=session_id,
                    tags=tags,
                )
                raise
        return wrapper

    def get_traces(
        self,
        limit: int = 50,
        span_type: str = None,
        model: str = None,
        agent: str = None,
        error_only: bool = False,
    ) -> list[dict]:
        traces = self._traces
        if span_type:
            traces = [t for t in traces if t.span_type == span_type]
        if model:
            traces = [t for t in traces if model.lower() in t.model.lower()]
        if agent:
            traces = [t for t in traces if agent.lower() in t.agent.lower()]
        if error_only:
            traces = [t for t in traces if t.error]
        return [t.to_dict() for t in traces[-limit:]]

    def get_cost_summary(self, days: int = 7) -> dict:
        cutoff = datetime.now() - timedelta(days=days)
        recent = [t for t in self._traces if t.timestamp >= cutoff]
        total_cost = sum(t.cost for t in recent)
        total_tokens = sum(t.tokens_in + t.tokens_out for t in recent)
        total_calls = len(recent)
        avg_latency = sum(t.latency_ms for t in recent) / total_calls if total_calls > 0 else 0
        errors = len([t for t in recent if t.error])

        by_model = {}
        for t in recent:
            if t.model not in by_model:
                by_model[t.model] = {"calls": 0, "cost": 0, "tokens": 0}
            by_model[t.model]["calls"] += 1
            by_model[t.model]["cost"] += t.cost
            by_model[t.model]["tokens"] += t.tokens_in + t.tokens_out

        return {
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "total_calls": total_calls,
            "avg_latency_ms": round(avg_latency, 1),
            "error_count": errors,
            "error_rate": round(errors / total_calls, 3) if total_calls > 0 else 0,
            "by_model": by_model,
            "period_days": days,
        }

    def get_latency_stats(self) -> dict:
        latencies = [t.latency_ms for t in self._traces if t.latency_ms > 0]
        if not latencies:
            return {"avg": 0, "p50": 0, "p95": 0, "p99": 0}

        latencies.sort()
        n = len(latencies)
        return {
            "avg": round(sum(latencies) / n, 1),
            "p50": round(latencies[int(n * 0.5)], 1),
            "p95": round(latencies[int(n * 0.95)], 1),
            "p99": round(latencies[int(n * 0.99)], 1),
            "min": round(latencies[0], 1),
            "max": round(latencies[-1], 1),
        }

    def get_quality_trend(self) -> list[dict]:
        scored = [t for t in self._traces if t.quality_score > 0]
        if not scored:
            return []
        batches = []
        batch_size = 20
        for i in range(0, len(scored), batch_size):
            batch = scored[i:i + batch_size]
            batches.append({
                "batch": i // batch_size + 1,
                "avg_quality": round(sum(t.quality_score for t in batch) / len(batch), 3),
                "count": len(batch),
            })
        return batches

    def export_traces(self, limit: int = 1000) -> str:
        return json.dumps([t.to_dict() for t in self._traces[-limit:]], indent=2)

    def get_stats(self) -> dict:
        return {
            "total_traces": len(self._traces),
            "max_traces": self._max_traces,
            "traces_file": str(TRACES_FILE),
        }

    def _load(self) -> None:
        if TRACES_FILE.exists():
            try:
                data = json.loads(TRACES_FILE.read_text(encoding="utf-8"))
                for t_data in data:
                    trace = Trace(
                        trace_id=t_data["trace_id"],
                        span_type=t_data["span_type"],
                        model=t_data.get("model", ""),
                        prompt=t_data.get("prompt_preview", ""),
                        response=t_data.get("response_preview", ""),
                        tokens_in=t_data.get("tokens_in", 0),
                        tokens_out=t_data.get("tokens_out", 0),
                        latency_ms=t_data.get("latency_ms", 0.0),
                        cost=t_data.get("cost", 0.0),
                        agent=t_data.get("agent", ""),
                        session_id=t_data.get("session_id", ""),
                        tags=t_data.get("tags", []),
                        quality_score=t_data.get("quality_score", 0.0),
                        error=t_data.get("error", ""),
                    )
                    if "timestamp" in t_data:
                        trace.timestamp = datetime.fromisoformat(t_data["timestamp"])
                    self._traces.append(trace)
            except Exception:
                pass

    def _save_traces(self) -> None:
        try:
            TRACES_FILE.write_text(json.dumps([t.to_dict() for t in self._traces[-self._max_traces:]], indent=2), encoding="utf-8")
        except Exception:
            pass


_global_observability: Optional[ObservabilityEngine] = None


def get_observability_engine() -> ObservabilityEngine:
    global _global_observability
    if _global_observability is None:
        _global_observability = ObservabilityEngine()
    return _global_observability
