"""
Subagent Spawning & Auxiliary Model Router v1.0
Enables zero-context-cost parallel workstreams and smart model routing.
SLMs for routine tasks, LLMs for complex reasoning.
"""

from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from threading import Lock
import time
import uuid


class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ModelTier(str, Enum):
    SLM = "slm"
    LLM = "llm"


@dataclass
class SubagentTask:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    prompt: str = ""
    complexity: TaskComplexity = TaskComplexity.MODERATE
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    result: Optional[Any] = None
    error: Optional[str] = None
    status: str = "pending"


@dataclass
class ModelRoute:
    task_id: str
    selected_model: str
    tier: ModelTier
    reason: str
    confidence: float = 0.0
    latency_ms: float = 0.0


class AuxiliaryModelRouter:
    """
    Routes tasks to appropriate model tier based on complexity.
    SLMs (Phi-4, Qwen3) for 95% routine tasks.
    LLMs (Gemini, GPT-4) for complex reasoning.
    """

    def __init__(self, transport_layer=None):
        self.transport_layer = transport_layer
        self._route_history = []
        self._lock = Lock()

    SLM_KEYWORDS = {
        "classify", "summarize", "extract", "format", "count",
        "list", "check", "validate", "parse", "translate",
        "simple", "basic", "routine", "repeat", "standard",
    }

    LLM_KEYWORDS = {
        "reason", "analyze", "design", "architect", "debug",
        "complex", "novel", "creative", "synthesize", "evaluate",
        "compare", "strategy", "optimize", "refactor", "plan",
    }

    def route_task(self, description: str, prompt: str) -> ModelRoute:
        start_time = time.time()

        text = f"{description} {prompt}".lower()
        slm_score = sum(1 for kw in self.SLM_KEYWORDS if kw in text)
        llm_score = sum(1 for kw in self.LLM_KEYWORDS if kw in text)

        is_long = len(prompt) > 1000
        has_code = any(x in text for x in ["def ", "class ", "import ", "function ", "=>"])
        has_math = any(x in text for x in ["calculate", "compute", "equation", "algorithm"])

        if llm_score > slm_score or is_long or (has_code and has_math):
            tier = ModelTier.LLM
            model = "gemini"
            reason = "Complex task requiring deep reasoning"
            confidence = 0.85
        else:
            tier = ModelTier.SLM
            model = "local"
            reason = "Simple task suitable for SLM"
            confidence = 0.90

        if llm_score == 0 and slm_score == 0:
            tier = ModelTier.SLM
            model = "local"
            reason = "Default routing to SLM"
            confidence = 0.70

        latency_ms = (time.time() - start_time) * 1000

        route = ModelRoute(
            task_id=str(uuid.uuid4())[:8],
            selected_model=model,
            tier=tier,
            reason=reason,
            confidence=round(confidence, 2),
            latency_ms=round(latency_ms, 2),
        )

        with self._lock:
            self._route_history.append(route)

        return route

    def get_routing_stats(self) -> dict:
        with self._lock:
            if not self._route_history:
                return {"total_routes": 0}

            slm_count = sum(1 for r in self._route_history if r.tier == ModelTier.SLM)
            llm_count = sum(1 for r in self._route_history if r.tier == ModelTier.LLM)
            total = len(self._route_history)

            return {
                "total_routes": total,
                "slm_routes": slm_count,
                "llm_routes": llm_count,
                "slm_pct": round(slm_count / total * 100, 1) if total else 0,
                "llm_pct": round(llm_count / total * 100, 1) if total else 0,
            }


class SubagentSpawner:
    """
    Manages parallel subagent execution with zero context cost.
    Each subagent runs in its own thread with isolated context.
    """

    def __init__(self, max_workers: int = 4, execute_fn: Optional[Callable] = None):
        self.max_workers = max_workers
        self.execute_fn = execute_fn
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks = {}
        self._lock = Lock()
        self._running = True

    def spawn(
        self,
        description: str,
        prompt: str,
        complexity: TaskComplexity = TaskComplexity.MODERATE,
        priority: int = 1,
    ) -> str:
        task = SubagentTask(
            description=description,
            prompt=prompt,
            complexity=complexity,
            priority=priority,
        )

        with self._lock:
            self._tasks[task.task_id] = task

        if self.execute_fn:
            future = self._executor.submit(self._run_task, task)
            future.add_done_callback(lambda f: self._on_complete(task.task_id, f))
        else:
            task.status = "pending_no_executor"

        return task.task_id

    def spawn_batch(
        self,
        tasks: list[dict],
    ) -> list[str]:
        ids = []
        for t in tasks:
            task_id = self.spawn(
                description=t.get("description", ""),
                prompt=t.get("prompt", ""),
                complexity=TaskComplexity(t.get("complexity", "moderate")),
                priority=t.get("priority", 1),
            )
            ids.append(task_id)
        return ids

    def get_result(self, task_id: str) -> Optional[Any]:
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                return task.result
        return None

    def get_status(self, task_id: str) -> dict:
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                return {
                    "task_id": task.task_id,
                    "status": task.status,
                    "description": task.description,
                    "created_at": task.created_at.isoformat(),
                    "error": task.error,
                }
        return {"error": "Task not found"}

    def get_all_statuses(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "task_id": t.task_id,
                    "status": t.status,
                    "description": t.description,
                    "created_at": t.created_at.isoformat(),
                }
                for t in self._tasks.values()
            ]

    def wait_all(self, timeout: Optional[float] = None) -> dict:
        print(f"[SubagentRouter] wait_all called")
        results = {}
        start_time = time.time()

        task_ids = []
        with self._lock:
            task_ids = list(self._tasks.keys())

        for task_id in task_ids:
            task = self._tasks.get(task_id)
            if not task:
                continue
            while task.status in ("pending", "running"):
                if timeout and (time.time() - start_time) > timeout:
                    break
                time.sleep(0.1)
            if task.status == "completed":
                results[task_id] = task.result
            elif task.error:
                results[task_id] = {"error": task.error}

        return results

    def shutdown(self) -> None:
        self._running = False
        self._executor.shutdown(wait=False)

    def _run_task(self, task: SubagentTask) -> Any:
        task.status = "running"
        try:
            if self.execute_fn:
                result = self.execute_fn(task.prompt, task.description)
                task.result = result
                task.status = "completed"
            else:
                task.status = "no_executor"
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
        return task.result

    def _on_complete(self, task_id: str, future: Future) -> None:
        try:
            future.result()
        except Exception as e:
            with self._lock:
                task = self._tasks.get(task_id)
                if task:
                    task.error = str(e)
                    task.status = "failed"

    @property
    def pending_count(self) -> int:
        with self._lock:
            return sum(1 for t in self._tasks.values() if t.status == "pending")

    @property
    def completed_count(self) -> int:
        with self._lock:
            return sum(1 for t in self._tasks.values() if t.status == "completed")


_global_router: Optional[AuxiliaryModelRouter] = None
_global_spawner: Optional[SubagentSpawner] = None
_init_lock = Lock()


def get_model_router(transport_layer=None) -> AuxiliaryModelRouter:
    global _global_router
    if _global_router is None:
        with _init_lock:
            if _global_router is None:
                _global_router = AuxiliaryModelRouter(transport_layer)
    return _global_router


def get_subagent_spawner(execute_fn: Optional[Callable] = None) -> SubagentSpawner:
    global _global_spawner
    if _global_spawner is None:
        with _init_lock:
            if _global_spawner is None:
                _global_spawner = SubagentSpawner(execute_fn=execute_fn)
    return _global_spawner
