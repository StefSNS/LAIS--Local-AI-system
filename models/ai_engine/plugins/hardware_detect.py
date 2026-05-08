"""
hardware_detect.py — Cherry-picked from OpenJarvis core/config.py
Auto-detects hardware and recommends the best model for our 3-AI team.

Usage:
    from system.hardware_detect import detect_hardware, recommend_model, can_load_model
    
    hw = detect_hardware()
    model = recommend_model(hw)
    if can_load_model("qwen3.5", hw):
        load_model("qwen3.5")
"""

import os
import platform
from dataclasses import dataclass
from typing import Optional


@dataclass
class GPUInfo:
    vendor: str = ""  # "nvidia", "amd", "intel", "apple"
    name: str = ""
    vram_gb: float = 0.0
    count: int = 0


@dataclass
class HardwareInfo:
    platform: str = ""
    cpu_brand: str = ""
    cpu_count: int = 0
    ram_gb: float = 0.0
    available_ram_gb: float = 0.0
    gpu: Optional[GPUInfo] = None


def _detect_cpu_brand() -> str:
    """Detect CPU brand from platform-specific sources."""
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            brand = winreg.QueryValueEx(key, "ProcessorNameString")[0]
            winreg.CloseKey(key)
            return brand.strip()
        except Exception:
            pass
    elif platform.system() == "Darwin":
        try:
            import subprocess
            result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                    capture_output=True, text=True)
            return result.stdout.strip()
        except Exception:
            pass
    else:
        try:
            info = {}
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if ":" in line:
                        key, val = line.split(":", 1)
                        info[key.strip()] = val.strip()
            return info.get("model name", "unknown")
        except Exception:
            pass
    return "unknown"


def _detect_nvidia_gpu() -> Optional[GPUInfo]:
    """Detect NVIDIA GPU via pynvml or nvidia-smi."""
    # Try pynvml first
    try:
        from pynvml import nvmlInit, nvmlDeviceGetCount, nvmlDeviceGetHandleByIndex
        from pynvml import nvmlDeviceGetName, nvmlDeviceGetMemoryInfo
        nvmlInit()
        count = nvmlDeviceGetCount()
        if count > 0:
            handle = nvmlDeviceGetHandleByIndex(0)
            name = nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode("utf-8")
            mem = nvmlDeviceGetMemoryInfo(handle)
            return GPUInfo(
                vendor="nvidia",
                name=name,
                vram_gb=mem.total / (1024**3),
                count=count,
            )
    except Exception:
        pass

    # Fallback to nvidia-smi
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            parts = lines[0].split(",")
            return GPUInfo(
                vendor="nvidia",
                name=parts[0].strip(),
                vram_gb=float(parts[1].strip().replace("MiB", "")) / 1024,
                count=len(lines),
            )
    except Exception:
        pass

    return None


def _detect_amd_gpu() -> Optional[GPUInfo]:
    """Detect AMD GPU via rocm-smi."""
    try:
        import subprocess
        result = subprocess.run(
            ["rocm-smi", "--showproductname", "--showmeminfo", "vram"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return GPUInfo(vendor="amd", name="AMD GPU", vram_gb=0, count=1)
    except Exception:
        pass
    return None


def _total_ram_gb() -> float:
    """Get total system RAM in GB."""
    try:
        import psutil
        return psutil.virtual_memory().total / (1024**3)
    except ImportError:
        pass

    if platform.system() == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulonglong = ctypes.c_ulonglong
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", c_ulonglong),
                    ("ullAvailPhys", c_ulonglong),
                    ("ullTotalPageFile", c_ulonglong),
                    ("ullAvailPageFile", c_ulonglong),
                    ("ullTotalVirtual", c_ulonglong),
                    ("ullAvailVirtual", c_ulonglong),
                    ("ullAvailExtendedVirtual", c_ulonglong),
                ]
            mem = MEMORYSTATUSEX()
            mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
            return mem.ullTotalPhys / (1024**3)
        except Exception:
            pass
    elif platform.system() == "Darwin":
        try:
            import subprocess
            result = subprocess.run(["sysctl", "-n", "hw.memsize"],
                                    capture_output=True, text=True)
            return int(result.stdout.strip()) / (1024**3)
        except Exception:
            pass
    else:
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        kb = int(line.split()[1])
                        return kb / (1024**2)
        except Exception:
            pass

    return 0.0


def _available_ram_gb() -> float:
    """Get currently available RAM in GB."""
    try:
        import psutil
        return psutil.virtual_memory().available / (1024**3)
    except ImportError:
        return _total_ram_gb() - 4.0  # rough estimate


def detect_hardware() -> HardwareInfo:
    """Auto-detect hardware with graceful fallbacks."""
    gpu = _detect_nvidia_gpu() or _detect_amd_gpu()
    return HardwareInfo(
        platform=platform.system().lower(),
        cpu_brand=_detect_cpu_brand(),
        cpu_count=os.cpu_count() or 1,
        ram_gb=_total_ram_gb(),
        available_ram_gb=_available_ram_gb(),
        gpu=gpu,
    )


# Model registry with RAM requirements
MODEL_REGISTRY = {
    "qwen3.5": {"ram_gb": 2.5, "strength": "code, reasoning", "type": "local"},
    "rwkv7": {"ram_gb": 1.5, "strength": "streaming, chat", "type": "local"},
    "smol3": {"ram_gb": 2.0, "strength": "general, fast", "type": "local"},
    "whisper-small": {"ram_gb": 0.5, "strength": "speech-to-text", "type": "local"},
    "gemini-2.5-flash": {"ram_gb": 0.0, "strength": "cloud reasoning", "type": "cloud"},
}


def recommend_model(hw: HardwareInfo, task_type: str = "general") -> dict:
    """Recommend the best model for detected hardware and task type."""
    available = hw.available_ram_gb

    # Cloud models always available (no RAM)
    if task_type in ("reasoning", "complex", "creative"):
        return {
            "model": "gemini-2.5-flash",
            "ram_needed": 0,
            "reason": "Cloud model — best for complex reasoning, no local RAM needed",
            "type": "cloud",
        }

    # Local model selection based on available RAM
    candidates = []
    for name, info in MODEL_REGISTRY.items():
        if info["type"] == "cloud":
            continue
        if info["ram_gb"] <= available - 0.5:  # 0.5GB safety margin
            candidates.append((name, info))

    if not candidates:
        return {
            "model": "gemini-2.5-flash",
            "ram_needed": 0,
            "reason": f"Only {available:.1f}GB available — no local model fits, using cloud",
            "type": "cloud",
        }

    # Sort by RAM usage (prefer smaller when RAM is tight)
    candidates.sort(key=lambda x: x[1]["ram_gb"])

    if task_type == "code":
        # Prefer Qwen for code if it fits
        for name, info in candidates:
            if "qwen" in name.lower():
                return {
                    "model": name,
                    "ram_needed": info["ram_gb"],
                    "reason": f"Best for code generation, {info['ram_gb']}GB RAM",
                    "type": "local",
                }

    best_name, best_info = candidates[0]
    return {
        "model": best_name,
        "ram_needed": best_info["ram_gb"],
        "reason": f"Fits in available RAM ({available:.1f}GB), strength: {best_info['strength']}",
        "type": "local",
    }


def can_load_model(model_name: str, hw: Optional[HardwareInfo] = None) -> bool:
    """Check if a model can be loaded with current RAM."""
    if hw is None:
        hw = detect_hardware()

    if model_name not in MODEL_REGISTRY:
        return False

    info = MODEL_REGISTRY[model_name]
    if info["type"] == "cloud":
        return True

    needed = info["ram_gb"]
    available = hw.available_ram_gb
    return available >= (needed + 0.5)  # 0.5GB safety margin


def format_hardware_report(hw: Optional[HardwareInfo] = None) -> str:
    """Format a human-readable hardware report."""
    if hw is None:
        hw = detect_hardware()

    lines = [
        f"Platform: {hw.platform}",
        f"CPU: {hw.cpu_brand} ({hw.cpu_count} cores)",
        f"RAM: {hw.ram_gb:.1f}GB total, {hw.available_ram_gb:.1f}GB available",
    ]

    if hw.gpu:
        lines.append(f"GPU: {hw.gpu.vendor} {hw.gpu.name} ({hw.gpu.vram_gb:.1f}GB VRAM x{hw.gpu.count})")
    else:
        lines.append("GPU: None detected (CPU-only inference)")

    rec = recommend_model(hw)
    lines.append(f"Recommended: {rec['model']} — {rec['reason']}")

    return "\n".join(lines)


if __name__ == "__main__":
    print("=== Hardware Detection ===")
    hw = detect_hardware()
    print(format_hardware_report(hw))
    print()
    print("=== Model Compatibility ===")
    for name in MODEL_REGISTRY:
        compatible = can_load_model(name, hw)
        ram = MODEL_REGISTRY[name]["ram_gb"]
        status = "OK" if compatible else "NO"
        print(f"  {status} {name} ({ram}GB)")
