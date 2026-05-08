"""
Dynamic Memory Reclaimer v1.0
Monitors system RAM and auto-unloads models when pressure is detected.
Based on LocalAI memory management patterns.
"""

import threading
import time
from datetime import datetime
from typing import Optional, Callable


class MemoryStats:
    """System memory snapshot."""

    def __init__(self, total: int, used: int, available: int, percent: float):
        self.total = total
        self.used = used
        self.available = available
        self.percent = percent
        self.timestamp = datetime.now()

    @property
    def usage_pct(self) -> float:
        return self.percent

    def to_dict(self) -> dict:
        return {
            "total_mb": round(self.total / 1024 / 1024, 1),
            "used_mb": round(self.used / 1024 / 1024, 1),
            "available_mb": round(self.available / 1024 / 1024, 1),
            "percent": round(self.percent, 1),
            "timestamp": self.timestamp.isoformat(),
        }


class MemoryReclaimer:
    """
    Monitors RAM usage and triggers reclaim actions when thresholds are crossed.

    Thresholds:
        - HIGH (70%): Clear caches, compress history
        - CRITICAL (85%): Unload least-recently-used local models
        - EMERGENCY (95%): Unload all local models, keep only cloud transport
    """

    HIGH = 70.0
    CRITICAL = 85.0
    EMERGENCY = 95.0

    def __init__(
        self,
        unload_local_fn: Optional[Callable] = None,
        compress_history_fn: Optional[Callable] = None,
        clear_cache_fn: Optional[Callable] = None,
        check_interval_seconds: float = 10.0,
    ):
        self.unload_local_fn = unload_local_fn
        self.compress_history_fn = compress_history_fn
        self.clear_cache_fn = clear_cache_fn
        self.check_interval = check_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._history = []
        self._max_history = 100
        self._reclaim_count = 0
        self._last_reclaim: Optional[datetime] = None
        self._last_level = "ok"

    def start(self) -> None:
        """Start background memory monitoring."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop background monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def get_stats(self) -> MemoryStats:
        """Get current memory stats."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return MemoryStats(mem.total, mem.used, mem.available, mem.percent)
        except ImportError:
            return MemoryStats(0, 0, 0, 0.0)

    def check_and_reclaim(self) -> str:
        """
        Check current memory and trigger reclaim if needed.
        Returns: 'ok', 'high', 'critical', or 'emergency'
        """
        stats = self.get_stats()
        self._history.append(stats)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        usage = stats.usage_pct
        level = "ok"

        if usage >= self.EMERGENCY:
            level = "emergency"
            self._execute_emergency()
        elif usage >= self.CRITICAL:
            level = "critical"
            self._execute_critical()
        elif usage >= self.HIGH:
            level = "high"
            self._execute_high()

        if level != "ok" and level != self._last_level:
            self._reclaim_count += 1
            self._last_reclaim = datetime.now()
            self._last_level = level

        return level

    def _execute_high(self) -> None:
        """Clear caches and compress history."""
        if self.clear_cache_fn:
            try:
                self.clear_cache_fn()
            except Exception:
                pass
        if self.compress_history_fn:
            try:
                self.compress_history_fn()
            except Exception:
                pass

    def _execute_critical(self) -> None:
        """Execute high-level reclaim + unload least-recently-used model."""
        self._execute_high()
        if self.unload_local_fn:
            try:
                self.unload_local_fn(mode="lru")
            except Exception:
                pass

    def _execute_emergency(self) -> None:
        """Execute critical-level reclaim + unload ALL local models."""
        self._execute_critical()
        if self.unload_local_fn:
            try:
                self.unload_local_fn(mode="all")
            except Exception:
                pass

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._running:
            try:
                self.check_and_reclaim()
            except Exception:
                pass
            time.sleep(self.check_interval)

    def get_history(self, limit: int = 20) -> list[dict]:
        """Get recent memory history."""
        return [s.to_dict() for s in self._history[-limit:]]

    def get_status(self) -> dict:
        """Get reclaimer status."""
        stats = self.get_stats()
        return {
            "running": self._running,
            "current_memory": stats.to_dict(),
            "reclaim_count": self._reclaim_count,
            "last_reclaim": self._last_reclaim.isoformat() if self._last_reclaim else None,
            "last_level": self._last_level,
            "thresholds": {
                "high": self.HIGH,
                "critical": self.CRITICAL,
                "emergency": self.EMERGENCY,
            },
        }


_global_reclaimer: Optional[MemoryReclaimer] = None


def get_memory_reclaimer(
    unload_local_fn: Optional[Callable] = None,
    compress_history_fn: Optional[Callable] = None,
    clear_cache_fn: Optional[Callable] = None,
) -> MemoryReclaimer:
    global _global_reclaimer
    if _global_reclaimer is None:
        _global_reclaimer = MemoryReclaimer(
            unload_local_fn=unload_local_fn,
            compress_history_fn=compress_history_fn,
            clear_cache_fn=clear_cache_fn,
        )
    return _global_reclaimer
