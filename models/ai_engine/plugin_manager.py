import importlib
import os
import sys
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGINS_DIR = os.path.join(BASE_DIR, "plugins")

plugins = {}

def clear_plugin_cache():
    """Remove all __pycache__ folders in plugins/ before loading."""
    pycache = os.path.join(PLUGINS_DIR, "__pycache__")
    if os.path.exists(pycache):
        shutil.rmtree(pycache)
    # Also clear any .pyc files
    for f in os.listdir(PLUGINS_DIR):
        if f.endswith(".pyc"):
            os.remove(os.path.join(PLUGINS_DIR, f))

def load_all():
    """Load all plugins. Clear cache first. Skip broken ones instead of crashing."""
    clear_plugin_cache()
    
    for f in os.listdir(PLUGINS_DIR):
        if f.endswith(".py") and f != "__init__.py":
            name = f[:-3]
            try:
                plugins[name] = importlib.import_module(f"plugins.{name}")
                print(f"[Loaded] {name}")
            except Exception as e:
                print(f"[Warning] Skipped '{name}': {e}")

class PluginReloader(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            name = os.path.basename(event.src_path)[:-3]
            try:
                # Clear the module from sys.modules to force fresh import
                if f"plugins.{name}" in sys.modules:
                    del sys.modules[f"plugins.{name}"]
                if name in plugins:
                    plugins[name] = importlib.reload(plugins[name])
                else:
                    plugins[name] = importlib.import_module(f"plugins.{name}")
                print(f"[Hot-Swap] Reloaded '{name}'")
            except Exception as e:
                print(f"[Hot-Swap Warning] Could not reload '{name}': {e}")

def start_watcher():
    observer = Observer()
    observer.schedule(PluginReloader(), PLUGINS_DIR)
    observer.daemon = True
    observer.start()