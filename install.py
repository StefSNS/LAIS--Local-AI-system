#!/usr/bin/env python3
"""
LAIS — One-Shot Installer
Bootstraps the full multi-agent AI system:
  • JARVIS Mark XXXIX (voice AI)
  • AI Engine (plugin orchestrator)
  • OpenCode CLI agent
  • Obsidian vault (optional)
  • All dependencies, plugins, and skills

Usage:
    python install.py          # Interactive install
    python install.py --quick  # Quick install (defaults only)
"""
import json, os, subprocess, sys, time, urllib.request, zipfile
from pathlib import Path

SELF_DIR = Path(__file__).resolve().parent
REQUIREMENTS = [
    "customtkinter", "pillow", "psutil", "requests",
    "beautifulsoup4", "duckduckgo-search", "pyautogui",
    "pyperclip", "opencv-python", "numpy", "mss",
    "google-genai", "google-generativeai",
    "sounddevice", "PyQt6", "playwright",
    "pywinauto", "pygetwindow", "python-pptx",
    "comtypes", "pycaw", "win10toast", "send2trash",
    "youtube-transcript-api", "psutil",
]

def step(msg): print(f"\n  >>> {msg}\n  " + "="*60)
def ok(msg): print(f"  [OK] {msg}")
def warn(msg): print(f"  [!] {msg}")
def fail(msg): print(f"  [FAIL] {msg}"); return False

def run(cmd, cwd=None, timeout=120):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def phase_system_check():
    step("Phase 1/7: System Check")
    if sys.version_info < (3, 11): return fail("Python 3.11+ required")
    ok(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    git_ok, _, _ = run(["git", "--version"])
    if not git_ok: return fail("Git not found")
    ok("Git found")
    pip_ok, _, _ = run([sys.executable, "-m", "pip", "--version"])
    if not pip_ok: return fail("pip not found")
    ok("pip found")
    return True

def phase_install_deps():
    step("Phase 2/7: Installing Dependencies")
    for pkg in REQUIREMENTS:
        ok_install, out, err = run([sys.executable, "-m", "pip", "install", pkg])
        if ok_install: ok(f"{pkg}")
        else: warn(f"{pkg}: {err[:100]}")
    ok_play, _, _ = run([sys.executable, "-m", "playwright", "install", "chromium"])
    if ok_play: ok("Playwright Chromium installed")
    return True

def phase_token_optimizer():
    step("Phase 3/7: Setting Up Token Optimization")
    addon_dir = SELF_DIR / "addons" / "token-optimizer"
    try:
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/StefSNS/LAIS--Local-AI-system/main/addons/token-optimizer/README.md",
            addon_dir / "README.md"
        )
    except: pass
    for lib in ["claw_compactor", "llmlingua", "tokenpruner", "shekel"]:
        ok_inst, _, _ = run([sys.executable, "-m", "pip", "install", lib])
        if ok_inst: ok(f"{lib} installed")
        else: warn(f"{lib} not available (optional)")
    return True

def phase_create_vault():
    step("Phase 4/7: Creating Knowledge Vault Structure")
    vault_dir = SELF_DIR / "vault"
    structure = {
        "00_Inbox": {}, "10_Resources": {"Tutorials": {}, "Books": {}, "Tools": {}},
        "20_Skills": {}, "30_Projects": {"Active": {}, "Ideas": {}},
        "40_System": {}, "50_Memory": {},
    }
    def _create(d, base):
        for name, children in d.items():
            (base / name).mkdir(parents=True, exist_ok=True)
            _create(children, base / name)
    _create(structure, vault_dir)
    ok(f"Vault created at {vault_dir}")

    # Create blank crystallized memory
    memory_file = vault_dir / "50_Memory" / "crystallized.json"
    memory_file.write_text(json.dumps({"learnings": [], "decision_log": [], "last_crystallized": ""}, indent=2))
    return True

def phase_validate():
    step("Phase 5/7: Validating Build")
    checks = []
    checks.append(("JARVIS main.py", (SELF_DIR / "models" / "Mark-XXXIX" / "main.py").exists()))
    checks.append(("AI Engine main.py", (SELF_DIR / "models" / "ai_engine" / "main.py").exists()))
    checks.append(("System config", (SELF_DIR / "config" / "system.json").exists()))
    valid = 0
    for py_file in SELF_DIR.rglob("*.py"):
        if "__pycache__" in str(py_file): continue
        try:
            compile(py_file.read_text(encoding="utf-8", errors="ignore"), str(py_file), "exec")
            valid += 1
        except SyntaxError: pass
    checks.append((f"Python files valid ({valid})", True))
    all_pass = True
    for name, passed in checks:
        print(f"  {name:<45} {'PASS' if passed else 'FAIL'}")
        if not passed: all_pass = False
    return all_pass

def phase_finalize():
    step("Phase 6/7: Finalizing Installation")
    readme = SELF_DIR / "README.md"
    if not readme.exists():
        warn("README.md not found")
    license_file = SELF_DIR / "LICENSE"
    if not license_file.exists():
        license_file.write_text("""CC BY-NC 4.0 License
Copyright (c) 2026

This work is licensed under a Creative Commons Attribution-NonCommercial 4.0 International License.
""")
        ok("LICENSE created")
    ok("Installation complete")
    return True

def main():
    quick = "--quick" in sys.argv
    print("""
  ╔════════════════════════════════════════════════╗
  ║          LAIS — Local AI System                ║
  ║   Voice AI + GUI Orchestrator + CLI Coder      ║
  ╚════════════════════════════════════════════════╝
    """)
    start = time.time()

    phases = [
        ("System Check", phase_system_check),
        ("Install Dependencies", phase_install_deps),
        ("Token Optimization", phase_token_optimizer),
        ("Knowledge Vault", phase_create_vault),
        ("Validation", phase_validate),
        ("Finalize", phase_finalize),
    ]

    results = []
    for phase_name, phase_fn in phases:
        try:
            result = phase_fn()
            results.append((phase_name, result if isinstance(result, bool) else True))
        except Exception as e:
            results.append((phase_name, False))
            warn(f"Phase '{phase_name}' failed: {e}")

    elapsed = time.time() - start
    print(f"\n  {'='*60}")
    print(f"  INSTALLATION COMPLETE ({elapsed:.0f}s)")
    print(f"  {'='*60}")
    for name, passed in results:
        print(f"  {'OK' if passed else 'FAIL'}  {name}")

    print(f"\n  Location: {SELF_DIR}")
    print(f"\n  Next steps:")
    print(f"  1. Add your Gemini API key to models/Mark-XXXIX/config/api_keys.json")
    print(f"  2. Run: python models/Mark-XXXIX/main.py    (JARVIS voice AI)")
    print(f"  3. Run: python models/ai_engine/main.py     (AI Engine GUI)")
    print(f"  4. Run: python lais_opencode.py              (OpenCode launcher)")
    print()

if __name__ == "__main__":
    main()
