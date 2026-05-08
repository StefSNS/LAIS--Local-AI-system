"""
RAM Manager - Smart model lifecycle management for 3GB constraint.
Handles loading/unloading models, monitoring usage, and optimizing for available memory.

Strategy:
- Qwen3.5-4B: Primary brain (always on when active)
- RWKV-7-3B: Long context specialist (load on demand, unload when idle)
- SmolLM3-3B: Creative fallback (disabled by default, manual load)
- Browsegrab + system: Always reserved ~1GB

Budget:
- Active: Qwen3.5 (2.5GB) + system (0.5GB) = 3.0GB
- With RWKV: Qwen3.5 (2.5GB) + RWKV (1.5GB) = 4.0GB (needs swap for one)
- Recommended: Run ONE model at a time, hot-swap as needed
"""

import os
import subprocess
import time
import psutil
import signal
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

# Resolve model directory (relative to project root)
_RAM_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAM_MODELS_DIR = os.path.join(_RAM_BASE, "models")

MODELS = {
    "qwen4": {
        "name": "Qwen3.5-4B",
        "path": os.path.join(_RAM_MODELS_DIR, "Qwen3.5-4B-Q4_K_M.gguf"),
        "port": 8101,
        "ram_mb": 2500,
        "role": "primary",
        "args": ["--ctx-size", "4096", "--threads", "6"],
    },
    "rwkv7": {
        "name": "RWKV-7-Goose-3B",
        "path": os.path.join(_RAM_MODELS_DIR, "rwkv7-2.9B-world-Q4_K_M.gguf"),
        "port": 8102,
        "ram_mb": 1500,
        "role": "specialist",
        "args": ["--ctx-size", "8192", "--threads", "6"],
    },
    "smol3": {
        "name": "SmolLM3-3B",
        "path": os.path.join(_RAM_MODELS_DIR, "HuggingFaceTB_SmolLM3-3B-Q4_K_M.gguf"),
        "port": 8100,
        "ram_mb": 2000,
        "role": "fallback",
        "args": ["--ctx-size", "4096", "--threads", "6"],
    },
}

LLAMA_SERVER = os.path.join(_RAM_MODELS_DIR, "llama-bin", "llama-server.exe")
RESERVED_RAM_MB = 500  # OS + system + browser buffer
TOTAL_RAM_MB = 3072    # 3GB target


class RAMManager:
    """Manages model lifecycle within 3GB RAM constraint."""

    def __init__(self):
        self.active_models: Dict[str, Dict] = {}
        self._load_existing_processes()

    def _load_existing_processes(self):
        """Detect already-running llama-server instances."""
        for proc in psutil.process_iter(["name", "cmdline", "pid"]):
            try:
                cmdline = " ".join(proc.info.get("cmdline", []) or [])
                if "llama-server" in cmdline:
                    for key, model in MODELS.items():
                        if f"--port {model['port']}" in cmdline:
                            self.active_models[key] = {
                                "pid": proc.info["pid"],
                                "ram_mb": self._get_process_ram_mb(proc.info["pid"]),
                                "process": proc,
                            }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def _get_process_ram_mb(self, pid: int) -> int:
        """Get RAM usage of a process in MB."""
        try:
            proc = psutil.Process(pid)
            return int(proc.memory_info().rss / (1024 * 1024))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0

    def get_system_ram(self) -> Dict[str, int]:
        """Get current system RAM usage."""
        mem = psutil.virtual_memory()
        return {
            "total_mb": int(mem.total / (1024 * 1024)),
            "used_mb": int(mem.used / (1024 * 1024)),
            "available_mb": int(mem.available / (1024 * 1024)),
            "percent": mem.percent,
        }

    def get_available_for_model(self) -> int:
        """Calculate how much RAM is available for a new model."""
        system = self.get_system_ram()
        active_model_ram = sum(m["ram_mb"] for m in self.active_models.values())
        return system["available_mb"] - RESERVED_RAM_MB

    def can_load_model(self, model_key: str) -> bool:
        """Check if we can load a model within RAM constraints."""
        if model_key in self.active_models:
            return True

        model = MODELS.get(model_key)
        if not model:
            return False

        available = self.get_available_for_model()
        return available >= model["ram_mb"]

    def load_model(self, model_key: str, timeout: int = 30) -> bool:
        """
        Load a model. Unloads conflicting models if RAM is tight.
        Returns True if model is running.
        """
        model = MODELS.get(model_key)
        if not model:
            return False

        if model_key in self.active_models:
            print(f"[RAMManager] {model['name']} already running on port {model['port']}")
            return True

        if not Path(model["path"]).exists():
            print(f"[RAMManager] Model file not found: {model['path']}")
            return False

        ram_needed = model["ram_mb"]
        available = self.get_available_for_model()

        if available < ram_needed:
            print(f"[RAMManager] Not enough RAM ({available}MB available, {ram_needed}MB needed)")
            print(f"[RAMManager] Attempting to unload low-priority models...")

            unloading = self._unload_lower_priority(model_key)
            time.sleep(2)
            available = self.get_available_for_model()

            if available < ram_needed:
                print(f"[RAMManager] Still insufficient RAM after unloading. Aborting.")
                return False

        cmd = [
            LLAMA_SERVER,
            "--model", model["path"],
            "--port", str(model["port"]),
            *model["args"],
        ]

        print(f"[RAMManager] Starting {model['name']} on port {model['port']}...")
        print(f"[RAMManager] Command: {' '.join(cmd)}")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            self.active_models[model_key] = {
                "pid": process.pid,
                "ram_mb": ram_needed,
                "process": process,
            }

            time.sleep(3)

            for i in range(timeout):
                if self._is_port_open(model["port"]):
                    print(f"[RAMManager] {model['name']} ready on port {model['port']}")
                    return True
                time.sleep(1)

            print(f"[RAMManager] Timeout waiting for {model['name']}")
            return False

        except Exception as e:
            print(f"[RAMManager] Failed to start {model['name']}: {e}")
            return False

    def unload_model(self, model_key: str) -> bool:
        """Unload a specific model."""
        if model_key not in self.active_models:
            print(f"[RAMManager] {model_key} is not running")
            return True

        model_data = self.active_models[model_key]
        model = MODELS[model_key]

        try:
            process = model_data["process"]
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

            del self.active_models[model_key]
            print(f"[RAMManager] Unloaded {model['name']} (freed ~{model['ram_mb']}MB)")
            return True

        except Exception as e:
            print(f"[RAMManager] Error unloading {model_key}: {e}")
            return False

    def unload_all(self) -> bool:
        """Unload all models."""
        keys = list(self.active_models.keys())
        for key in keys:
            self.unload_model(key)
        print("[RAMManager] All models unloaded")
        return True

    def switch_to(self, model_key: str) -> bool:
        """
        Smart switch: unload lower-priority models, load target.
        Priority: primary > specialist > fallback
        """
        priority_order = ["qwen4", "rwkv7", "smol3"]
        target_priority = priority_order.index(model_key) if model_key in priority_order else 99

        for key in list(self.active_models.keys()):
            if key == model_key:
                continue
            current_priority = priority_order.index(key) if key in priority_order else 99
            if current_priority >= target_priority:
                self.unload_model(key)

        return self.load_model(model_key)

    def _unload_lower_priority(self, target_key: str) -> List[str]:
        """Unload models with lower priority than target."""
        priority_order = {"qwen4": 3, "rwkv7": 2, "smol3": 1}
        target_priority = priority_order.get(target_key, 0)
        unloaded = []

        for key in list(self.active_models.keys()):
            if priority_order.get(key, 0) < target_priority:
                if self.unload_model(key):
                    unloaded.append(key)

        return unloaded

    def _is_port_open(self, port: int) -> bool:
        """Check if a port is listening."""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def get_status(self) -> Dict:
        """Get full RAM and model status."""
        system = self.get_system_ram()
        models_status = {}

        for key, model in MODELS.items():
            is_running = key in self.active_models
            models_status[key] = {
                "name": model["name"],
                "running": is_running,
                "port": model["port"],
                "ram_mb": model["ram_mb"],
                "actual_ram_mb": self.active_models[key]["ram_mb"] if is_running else 0,
                "role": model["role"],
            }

        active_ram = sum(m["ram_mb"] for m in self.active_models.values())
        used_for_budget = active_ram + RESERVED_RAM_MB

        return {
            "system": system,
            "models": models_status,
            "active_ram_mb": active_ram,
            "reserved_mb": RESERVED_RAM_MB,
            "total_budget_mb": TOTAL_RAM_MB,
            "headroom_mb": max(0, TOTAL_RAM_MB - used_for_budget),
            "budget_used_percent": round((used_for_budget / TOTAL_RAM_MB) * 100, 1),
            "timestamp": datetime.now().isoformat(),
        }

    def print_status(self):
        """Print human-readable status."""
        status = self.get_status()
        system = status["system"]

        print("=" * 60)
        print("RAM Manager Status")
        print("=" * 60)
        print(f"System RAM: {system['used_mb']}MB / {system['total_mb']}MB ({system['percent']}%)")
        print(f"Available: {system['available_mb']}MB")
        print(f"Model RAM (active): {status['active_ram_mb']}MB")
        print(f"Budget: {status['active_ram_mb']}MB + {RESERVED_RAM_MB}MB reserved = {status['active_ram_mb'] + RESERVED_RAM_MB}MB / {TOTAL_RAM_MB}MB ({status['budget_used_percent']}%)")
        print(f"Headroom: {status['headroom_mb']}MB")
        print()

        for key, model in status["models"].items():
            status_icon = "[RUNNING]" if model["running"] else "[STOPPED]"
            print(f"  {status_icon} {model['name']} (port {model['port']}) - {model['role']}")
            if model["running"]:
                print(f"           Actual RAM: {model['actual_ram_mb']}MB")
            else:
                print(f"           Estimated RAM: {model['ram_mb']}MB")

        print("=" * 60)


def load_ram_manager() -> RAMManager:
    """Factory function."""
    return RAMManager()


if __name__ == "__main__":
    manager = load_ram_manager()
    manager.print_status()

    import argparse
    parser = argparse.ArgumentParser(description="RAM Manager for LLM models")
    parser.add_argument("command", choices=["status", "load", "unload", "switch", "unload-all"],
                        help="Command to execute")
    parser.add_argument("--model", choices=["qwen4", "rwkv7", "smol3"],
                        help="Model to load/unload/switch to")
    args = parser.parse_args()

    if args.command == "status":
        manager.print_status()
    elif args.command == "load" and args.model:
        manager.load_model(args.model)
        manager.print_status()
    elif args.command == "unload" and args.model:
        manager.unload_model(args.model)
        manager.print_status()
    elif args.command == "switch" and args.model:
        manager.switch_to(args.model)
        manager.print_status()
    elif args.command == "unload-all":
        manager.unload_all()
        manager.print_status()
