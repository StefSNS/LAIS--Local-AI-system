"""
Hook System v1.0
Event-driven hooks on conversation lifecycle.

Hooks fire on: SessionStart, SessionEnd, PreTool, PostTool, PreResponse, PostResponse, Error, Idle.
"""

import time
import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from threading import Lock


class HookEvent(str, Enum):
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    PRE_TOOL = "pre_tool"
    POST_TOOL = "post_tool"
    PRE_RESPONSE = "pre_response"
    POST_RESPONSE = "post_response"
    PRE_PLAN = "pre_plan"
    POST_PLAN = "post_plan"
    ERROR = "error"
    IDLE = "idle"
    MEMORY_ADD = "memory_add"
    TOOL_REGISTER = "tool_register"
    AUTONOMY_CHANGE = "autonomy_change"


class HookResult:
    """Result of a hook execution."""

    def __init__(
        self,
        success: bool,
        hook_name: str,
        event: HookEvent,
        duration_ms: float = 0.0,
        output: Any = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.hook_name = hook_name
        self.event = event
        self.duration_ms = duration_ms
        self.output = output
        self.error = error


class HookContext:
    """Context passed to hook handlers."""

    def __init__(
        self,
        event: HookEvent,
        data: dict = None,
        agent_name: str = "",
        session_id: str = "",
    ):
        self.event = event
        self.data = data or {}
        self.agent_name = agent_name
        self.session_id = session_id
        self.timestamp = datetime.now()
        self.metadata: dict = {}

    def set_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)


class HookHandler:
    """A registered hook handler."""

    def __init__(
        self,
        name: str,
        event: HookEvent,
        handler_fn: Callable,
        priority: int = 100,
        enabled: bool = True,
    ):
        self.name = name
        self.event = event
        self.handler_fn = handler_fn
        self.priority = priority
        self.enabled = enabled
        self.call_count = 0
        self.last_called: Optional[datetime] = None
        self.total_duration_ms = 0.0
        self.error_count = 0

    def execute(self, context: HookContext) -> HookResult:
        if not self.enabled:
            return HookResult(False, self.name, self.event, error="disabled")

        start = time.time()
        try:
            output = self.handler_fn(context)
            duration_ms = (time.time() - start) * 1000
            self.call_count += 1
            self.last_called = datetime.now()
            self.total_duration_ms += duration_ms
            return HookResult(True, self.name, self.event, duration_ms, output)
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            self.error_count += 1
            return HookResult(False, self.name, self.event, duration_ms, error=str(e))


class HookRegistry:
    """Central registry for all hooks."""

    def __init__(self):
        self._hooks: dict[HookEvent, list[HookHandler]] = {e: [] for e in HookEvent}
        self._lock = Lock()

    def register(self, hook: HookHandler) -> None:
        with self._lock:
            self._hooks[hook.event].append(hook)
            self._hooks[hook.event].sort(key=lambda h: h.priority)

    def unregister(self, name: str, event: HookEvent) -> bool:
        with self._lock:
            before = len(self._hooks[event])
            self._hooks[event] = [h for h in self._hooks[event] if h.name != name]
            return len(self._hooks[event]) < before

    def get_hooks(self, event: HookEvent) -> list[HookHandler]:
        with self._lock:
            return [h for h in self._hooks[event] if h.enabled]

    def list_all(self) -> list[dict]:
        result = []
        for event, hooks in self._hooks.items():
            for h in hooks:
                result.append({
                    "name": h.name,
                    "event": h.event.value,
                    "enabled": h.enabled,
                    "priority": h.priority,
                    "call_count": h.call_count,
                    "error_count": h.error_count,
                })
        return result


class HookEngine:
    """
    Manages hook execution across the conversation lifecycle.
    """

    def __init__(self, registry: Optional[HookRegistry] = None):
        self.registry = registry or HookRegistry()
        self._execution_log = []
        self._lock = Lock()

    def fire(self, event: HookEvent, context: HookContext) -> list[HookResult]:
        """Fire all hooks for an event."""
        hooks = self.registry.get_hooks(event)
        results = []

        for hook in hooks:
            result = hook.execute(context)
            results.append(result)

            with self._lock:
                self._execution_log.append({
                    "hook": hook.name,
                    "event": event.value,
                    "success": result.success,
                    "duration_ms": result.duration_ms,
                    "error": result.error,
                    "timestamp": datetime.now().isoformat(),
                })

        return results

    def fire_and_continue(
        self,
        event: HookEvent,
        data: dict,
        agent_name: str = "",
        session_id: str = "",
    ) -> dict:
        """Fire hooks and return any metadata modifications."""
        context = HookContext(event, data, agent_name, session_id)
        results = self.fire(event, context)

        modified_data = dict(data)
        for r in results:
            if r.success and isinstance(r.output, dict):
                modified_data.update(r.output)

        return {
            "event": event.value,
            "hooks_fired": len(results),
            "success": all(r.success for r in results),
            "modified_data": modified_data,
            "errors": [r.error for r in results if r.error],
        }

    def on_event(self, event: HookEvent, name: str, priority: int = 100):
        """Decorator for registering hook handlers."""
        def decorator(fn: Callable) -> Callable:
            hook = HookHandler(name, event, fn, priority)
            self.registry.register(hook)
            return fn
        return decorator

    def register_builtin_hooks(self) -> None:
        """Register default built-in hooks."""
        self.registry.register(HookHandler(
            "log_session_start",
            HookEvent.SESSION_START,
            lambda ctx: self._log_hook(f"Session started: {ctx.session_id}"),
            priority=1,
        ))
        self.registry.register(HookHandler(
            "log_session_end",
            HookEvent.SESSION_END,
            lambda ctx: self._log_hook(f"Session ended: {ctx.session_id}"),
            priority=1,
        ))
        self.registry.register(HookHandler(
            "log_tool_call",
            HookEvent.POST_TOOL,
            lambda ctx: self._log_hook(f"Tool called: {ctx.data.get('tool_name', 'unknown')}"),
            priority=1,
        ))
        self.registry.register(HookHandler(
            "log_error",
            HookEvent.ERROR,
            lambda ctx: self._log_hook(f"Error: {ctx.data.get('error', 'unknown')}"),
            priority=1,
        ))

    def get_execution_log(self, limit: int = 50) -> list[dict]:
        with self._lock:
            return self._execution_log[-limit:]

    def get_stats(self) -> dict:
        with self._lock:
            total_hooks = sum(len(hooks) for hooks in self.registry._hooks.values())
            total_calls = sum(h.call_count for hooks in self.registry._hooks.values() for h in hooks)
            total_errors = sum(h.error_count for hooks in self.registry._hooks.values() for h in hooks)

            return {
                "total_registered": total_hooks,
                "total_calls": total_calls,
                "total_errors": total_errors,
                "error_rate": round(total_errors / total_calls, 3) if total_calls > 0 else 0,
                "events_with_hooks": sum(1 for hooks in self.registry._hooks.values() if hooks),
            }

    @staticmethod
    def _log_hook(message: str) -> dict:
        print(f"[Hook] {message}")
        return {"logged": True}


_global_engine: Optional[HookEngine] = None
_engine_lock = Lock()


def get_hook_engine() -> HookEngine:
    global _global_engine
    if _global_engine is None:
        with _engine_lock:
            if _global_engine is None:
                _global_engine = HookEngine()
                _global_engine.register_builtin_hooks()
    return _global_engine
