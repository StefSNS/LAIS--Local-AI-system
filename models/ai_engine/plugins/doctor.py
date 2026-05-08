"""
doctor.py â€” Cherry-picked from OpenJarvis CLI doctor command
Diagnostic tool for the 3-AI team ecosystem.

Usage:
    python -m plugins.doctor
    from plugins.doctor import run_doctor
    result = run_doctor()
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Mark-XXXV path: can override via JARVIS_PATH env variable
JARVIS_BASE = os.environ.get("JARVIS_PATH", r"%USERPROFILE%\Desktop\AI projects\Mark-XXXV")

def _check(description, fn):
    """Run a check and return (status, detail)."""
    try:
        ok, detail = fn()
        status = "OK" if ok else "WARN"
        return status, detail
    except Exception as e:
        return "FAIL", str(e)


def _check_python_version():
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 11
    return ok, f"Python {v.major}.{v.minor}.{v.micro} {'(3.11+)' if ok else '(need 3.11+)'}"


def _check_psutil():
    try:
        import psutil
        mem = psutil.virtual_memory()
        ok = mem.percent < 90
        return ok, f"RAM: {mem.used/1e9:.1f}GB / {mem.total/1e9:.1f}GB ({mem.percent}% used)"
    except ImportError:
        return False, "psutil not installed"


def _check_omnis():
    omnis = Path(r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis")
    if not omnis.exists():
        return False, "Omnis directory not found"
    main = omnis / "unified_layer" / "orchestrator.py"
    ok = main.exists()
    return ok, f"{'found' if ok else 'MISSING'}: {main.name}"


def _check_jarvis():
    jarvis = Path(JARVIS_BASE)
    if not jarvis.exists():
        return False, "Jarvis directory not found"
    main = jarvis / "main.py"
    ok = main.exists()
    return ok, f"{'found' if ok else 'MISSING'}: {main.name}"


def _check_voice():
    voice = Path(r"%USERPROFILE%\Desktop\AI projects\Mark-XXXIX")
    if not voice.exists():
        return True, "Not yet installed (planned: whisper-small + edge-tts)"
    vs = voice / "voice_system.py"
    ok = vs.exists()
    return ok, f"{'found' if ok else 'MISSING'}: {vs.name}"


def _check_vault():
    vault = Path(os.environ.get("OMNIS_VAULT_PATH", r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain"))
    if not vault.exists():
        return False, "Vault directory not found"
    notes = list(vault.rglob("*.md"))
    return True, f"{len(notes)} notes in vault"


def _check_txtai_index():
    idx = Path(r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\memory\txtai_index")
    if not idx.exists():
        return False, "Txtai index not found"
    embeddings = idx / "embeddings"
    ok = embeddings.exists()
    return ok, f"{'index exists' if ok else 'MISSING embeddings'}"


def _check_embeddings():
    emb = Path(r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis\unified_layer\embeddings.py")
    cache = Path(r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\memory\vault_embeddings.json")
    if not emb.exists():
        return False, "embeddings.py not found"
    if cache.exists():
        import json
        data = json.loads(cache.read_text())
        count = data.get("note_count", 0)
        return True, f"{count} notes embedded"
    return False, "No embeddings cache -- run build_embeddings()"


def _check_skills_opencode():
    skills = Path.home() / ".config" / "opencode" / "skills"
    if not skills.exists():
        return False, "OpenCode skills directory not found"
    skill_dirs = [d for d in skills.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
    return True, f"{len(skill_dirs)} skills installed"


def _check_skills_omnis():
    skills = Path(r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\central_skills")
    if not skills.exists():
        return False, "Omnis skills directory not found"
    skill_dirs = [d for d in skills.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
    return True, f"{len(skill_dirs)} skills installed"


def _check_skills_jarvis():
    skills = Path(JARVIS_BASE) / "skills"
    if not skills.exists():
        return False, "Jarvis skills directory not found"
    skill_dirs = [d for d in skills.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
    return True, f"{len(skill_dirs)} skills installed"


def _check_memory():
    mem = Path(JARVIS_BASE) / "memory" / "long_term.json"
    if not mem.exists():
        return False, "long_term.json not found"
    import json
    data = json.loads(mem.read_text())
    categories = {k: len(v) for k, v in data.items() if isinstance(v, dict)}
    total = sum(categories.values())
    return True, f"{total} entries across {len(categories)} categories: {categories}"


def _check_hardware():
    try:
        import sys
        from pathlib import Path
        omnis = Path(r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis")
        if str(omnis) not in sys.path:
            sys.path.insert(0, str(omnis))
        from plugins.hardware_detect import detect_hardware
        hw = detect_hardware()
        return True, f"{hw.cpu_brand} ({hw.cpu_count} cores), {hw.ram_gb:.1f}GB RAM, {hw.available_ram_gb:.1f}GB available"
    except Exception as e:
        return False, f"Hardware detection failed: {e}"


def run_doctor():
    """Run all diagnostic checks."""
    checks = [
        ("Python version", _check_python_version),
        ("System RAM", _check_psutil),
        ("Hardware detection", _check_hardware),
        ("Omnis core", _check_omnis),
        ("Jarvis core", _check_jarvis),
        ("Voice subsystem", _check_voice),
        ("Vault (Obsidian)", _check_vault),
        ("Txtai index", _check_txtai_index),
        ("Embeddings cache", _check_embeddings),
        ("Skills (OpenCode)", _check_skills_opencode),
        ("Skills (Omnis)", _check_skills_omnis),
        ("Skills (Jarvis)", _check_skills_jarvis),
        ("Memory (long_term.json)", _check_memory),
    ]

    print("=" * 60)
    print("3-AI Team Diagnostic Report")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = []
    for name, fn in checks:
        status, detail = _check(name, fn)
        results.append((name, status, detail))
        icon = {"OK": "PASS", "WARN": "WARN", "FAIL": "FAIL"}.get(status, "????")
        print(f"  [{icon}] {name}: {detail}")

    print("=" * 60)

    ok_count = sum(1 for _, s, _ in results if s == "OK")
    warn_count = sum(1 for _, s, _ in results if s == "WARN")
    fail_count = sum(1 for _, s, _ in results if s == "FAIL")

    print(f"Results: {ok_count} OK, {warn_count} WARN, {fail_count} FAIL")

    if fail_count > 0:
        print("\nFailed checks:")
        for name, status, detail in results:
            if status == "FAIL":
                print(f"  - {name}: {detail}")

    print("=" * 60)

    return {
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "ok": ok_count,
        "warn": warn_count,
        "fail": fail_count,
        "details": [(n, s, d) for n, s, d in results],
    }


if __name__ == "__main__":
    run_doctor()
