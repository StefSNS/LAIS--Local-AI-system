"""
Lightweight Plugin System v1.0
Externalized plugins with lifecycle hooks (init, execute, cleanup).
Based on OpenClaw plugin lifecycle pattern.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from threading import Lock
import importlib
import json


PLUGINS_DIR = Path(__file__).resolve().parent.parent / "plugins"
PLUGINS_DIR.mkdir(parents=True, exist_ok=True)


class PluginState(str, Enum):
    LOADED = "loaded"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


class PluginLifecycle:
    """Lifecycle hooks for plugins."""

    def on_init(self, config: dict) -> bool:
        return True

    def on_execute(self, *args, **kwargs) -> Any:
        return None

    def on_cleanup(self) -> None:
        pass


class PluginInfo:
    """Metadata for a registered plugin."""

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        author: str = "",
    ):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.state = PluginState.LOADED
        self.created_at = datetime.now()
        self.last_executed = None
        self.execution_count = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "last_executed": self.last_executed.isoformat() if self.last_executed else None,
            "execution_count": self.execution_count,
        }


class BasePlugin(ABC):
    """
    Abstract base for all plugins.
    Implements lifecycle hooks.
    """

    info: PluginInfo

    def __init__(self):
        self.info = PluginInfo(
            name=self.__class__.__name__,
        )

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        pass

    def on_load(self, config: dict) -> bool:
        return True

    def on_unload(self) -> None:
        pass


class PluginManager:
    """
    Manages plugin lifecycle: load, execute, unload.
    """

    def __init__(self, plugins_dir: Path = PLUGINS_DIR):
        self.plugins_dir = plugins_dir
        self._plugins = {}
        self._lock = Lock()

    def register(self, plugin: BasePlugin, config: Optional[dict] = None) -> bool:
        with self._lock:
            try:
                if not plugin.on_load(config or {}):
                    plugin.info.state = PluginState.ERROR
                    return False

                self._plugins[plugin.info.name] = plugin
                plugin.info.state = PluginState.LOADED
                return True
            except Exception as e:
                plugin.info.state = PluginState.ERROR
                print(f"[PluginManager] Failed to register {plugin.info.name}: {e}")
                return False

    def unregister(self, name: str) -> bool:
        with self._lock:
            plugin = self._plugins.get(name)
            if not plugin:
                return False

            try:
                plugin.on_unload()
                del self._plugins[name]
                return True
            except Exception as e:
                print(f"[PluginManager] Failed to unregister {name}: {e}")
                return False

    def execute(self, name: str, *args, **kwargs) -> Any:
        with self._lock:
            plugin = self._plugins.get(name)
            if not plugin:
                return None

            if plugin.info.state == PluginState.DISABLED:
                return None

        try:
            result = plugin.execute(*args, **kwargs)
            with self._lock:
                plugin.info.state = PluginState.ACTIVE
                plugin.info.last_executed = datetime.now()
                plugin.info.execution_count += 1
            return result
        except Exception as e:
            with self._lock:
                plugin.info.state = PluginState.ERROR
            print(f"[PluginManager] Execution error in {name}: {e}")
            return None

    def load_from_file(self, filepath: Path) -> Optional[BasePlugin]:
        try:
            spec = importlib.util.spec_from_file_location(filepath.stem, str(filepath))
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr != BasePlugin
                ):
                    return attr()
        except Exception as e:
            print(f"[PluginManager] Failed to load plugin from {filepath}: {e}")

        return None

    def discover_plugins(self) -> list[Path]:
        plugin_files = []
        for py_file in self.plugins_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            plugin_files.append(py_file)
        return plugin_files

    def load_all(self) -> int:
        count = 0
        for filepath in self.discover_plugins():
            plugin = self.load_from_file(filepath)
            if plugin:
                if self.register(plugin):
                    count += 1
        return count

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        return self._plugins.get(name)

    def list_plugins(self) -> list[dict]:
        with self._lock:
            return [p.info.to_dict() for p in self._plugins.values()]

    def get_stats(self) -> dict:
        with self._lock:
            states = {}
            for p in self._plugins.values():
                state = p.info.state.value
                states[state] = states.get(state, 0) + 1

            return {
                "total_plugins": len(self._plugins),
                "state_breakdown": states,
            }


_global_manager: Optional[PluginManager] = None
_manager_lock = Lock()


def get_plugin_manager() -> PluginManager:
    global _global_manager
    if _global_manager is None:
        with _manager_lock:
            if _global_manager is None:
                _global_manager = PluginManager()
    return _global_manager
