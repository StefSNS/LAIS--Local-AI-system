"""
task_presets.py — Cherry-picked from OpenJarvis recipe/preset pattern
Pre-configured task templates for common 3-AI team workflows.

Usage:
    from plugins.task_presets import list_presets, run_preset
    list_presets()
    result = run_preset("deep-research", {"topic": "AI agent architectures"})
"""

from pathlib import Path
from typing import Dict, Any, Optional, Callable, List


class TaskPreset:
    """A pre-configured task template."""
    def __init__(self, name: str, description: str, steps: List[Dict[str, Any]],
                 required_skills: Optional[List[str]] = None,
                 estimated_ram_gb: float = 0.0):
        self.name = name
        self.description = description
        self.steps = steps
        self.required_skills = required_skills or []
        self.estimated_ram_gb = estimated_ram_gb


# Preset Registry
PRESETS: Dict[str, TaskPreset] = {}


def register_preset(preset: TaskPreset):
    PRESETS[preset.name] = preset


# ── Deep Research Preset ──────────────────────────────────────────────
register_preset(TaskPreset(
    name="deep-research",
    description="Multi-hop research across vault + web with citations",
    required_skills=["brainstorming", "writing-plans"],
    estimated_ram_gb=2.5,
    steps=[
        {"step": 1, "action": "brainstorm", "desc": "Clarify research question, identify angles"},
        {"step": 2, "action": "vault_search", "desc": "Search vault for existing knowledge on topic"},
        {"step": 3, "action": "web_search", "desc": "Search web for current information"},
        {"step": 4, "action": "synthesize", "desc": "Combine vault + web findings with citations"},
        {"step": 5, "action": "write_note", "desc": "Create vault note with research summary"},
    ],
))


# ── Code Assistant Preset ─────────────────────────────────────────────
register_preset(TaskPreset(
    name="code-assistant",
    description="Agent with code execution, file I/O, and shell access",
    required_skills=["brainstorming", "writing-plans", "test-driven-development", "verification-before-completion"],
    estimated_ram_gb=2.5,
    steps=[
        {"step": 1, "action": "brainstorm", "desc": "Understand requirements, explore approaches"},
        {"step": 2, "action": "plan", "desc": "Write implementation plan with steps"},
        {"step": 3, "action": "write_tests", "desc": "Write tests first (TDD)"},
        {"step": 4, "action": "implement", "desc": "Write code to pass tests"},
        {"step": 5, "action": "verify", "desc": "Run tests, lint, typecheck"},
        {"step": 6, "action": "review", "desc": "Self-review against requirements"},
    ],
))


# ── Morning Digest Preset ─────────────────────────────────────────────
register_preset(TaskPreset(
    name="morning-digest",
    description="Daily briefing from memory, projects, and notes",
    required_skills=[],
    estimated_ram_gb=0.5,
    steps=[
        {"step": 1, "action": "load_memory", "desc": "Load long-term memory entries"},
        {"step": 2, "action": "recent_notes", "desc": "Find notes created/updated since last digest"},
        {"step": 3, "action": "summarize", "desc": "Create summary of key points"},
        {"step": 4, "action": "surface_wishes", "desc": "Remind user of pending wishes/goals"},
    ],
))


# ── Debug Session Preset ──────────────────────────────────────────────
register_preset(TaskPreset(
    name="debug-session",
    description="Structured debugging with systematic approach",
    required_skills=["systematic-debugging", "debug-assist"],
    estimated_ram_gb=2.0,
    steps=[
        {"step": 1, "action": "reproduce", "desc": "Understand and reproduce the bug"},
        {"step": 2, "action": "isolate", "desc": "Narrow down to minimal reproduction"},
        {"step": 3, "action": "hypothesize", "desc": "Generate hypotheses for root cause"},
        {"step": 4, "action": "test_hypotheses", "desc": "Test each hypothesis systematically"},
        {"step": 5, "action": "fix", "desc": "Implement fix for confirmed root cause"},
        {"step": 6, "action": "verify", "desc": "Verify fix, add regression test"},
    ],
))


# ── Architecture Design Preset ────────────────────────────────────────
register_preset(TaskPreset(
    name="architecture-design",
    description="System design with brainstorming, alternatives, and documentation",
    required_skills=["brainstorming", "architecture", "writing-plans"],
    estimated_ram_gb=2.5,
    steps=[
        {"step": 1, "action": "brainstorm", "desc": "Explore requirements, constraints, goals"},
        {"step": 2, "action": "alternatives", "desc": "Generate at least 2 architecture approaches"},
        {"step": 3, "action": "evaluate", "desc": "Compare approaches on trade-offs"},
        {"step": 4, "action": "decide", "desc": "Select approach with rationale"},
        {"step": 5, "action": "document", "desc": "Write architecture decision record in vault"},
    ],
))


# ── Security Audit Preset ─────────────────────────────────────────────
register_preset(TaskPreset(
    name="security-audit",
    description="Scan codebase for vulnerabilities and unsafe patterns",
    required_skills=["security-audit", "verification-before-completion"],
    estimated_ram_gb=2.0,
    steps=[
        {"step": 1, "action": "scan_secrets", "desc": "Search for hardcoded secrets, keys, tokens"},
        {"step": 2, "action": "scan_deps", "desc": "Check dependencies for known vulnerabilities"},
        {"step": 3, "action": "scan_patterns", "desc": "Look for unsafe patterns (SQLi, XSS, etc.)"},
        {"step": 4, "action": "scan_permissions", "desc": "Review file/network permission patterns"},
        {"step": 5, "action": "report", "desc": "Generate security report with severity levels"},
    ],
))


# ── Model Switch Preset ───────────────────────────────────────────────
register_preset(TaskPreset(
    name="model-switch",
    description="Smart model selection based on task type and RAM budget",
    required_skills=["model-switch"],
    estimated_ram_gb=0.0,
    steps=[
        {"step": 1, "action": "detect_hardware", "desc": "Check current RAM and available capacity"},
        {"step": 2, "action": "classify_task", "desc": "Determine if code/reasoning/voice/general"},
        {"step": 3, "action": "select_model", "desc": "Pick best model that fits RAM budget"},
        {"step": 4, "action": "unload_current", "desc": "Unload currently loaded model"},
        {"step": 5, "action": "load_new", "desc": "Load selected model and verify"},
    ],
))


def list_presets() -> List[Dict[str, str]]:
    """List all available presets."""
    return [
        {"name": p.name, "description": p.description, "steps": len(p.steps)}
        for p in PRESETS.values()
    ]


def get_preset(name: str) -> Optional[TaskPreset]:
    """Get a preset by name."""
    return PRESETS.get(name)


def run_preset(name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run a preset — returns the plan, doesn't execute it.
    
    The caller (Omnis orchestrator or Jarvis) executes the steps.
    """
    preset = PRESETS.get(name)
    if not preset:
        return {"error": f"Preset '{name}' not found", "available": list(PRESETS.keys())}
    
    return {
        "preset": preset.name,
        "description": preset.description,
        "steps": preset.steps,
        "required_skills": preset.required_skills,
        "estimated_ram_gb": preset.estimated_ram_gb,
        "context": context or {},
    }


if __name__ == "__main__":
    print("=== Task Presets ===")
    for p in list_presets():
        print(f"  {p['name']}: {p['description']} ({p['steps']} steps)")
    
    print("\n=== Example: deep-research ===")
    result = run_preset("deep-research", {"topic": "AI agent architectures"})
    print(f"Preset: {result['preset']}")
    print(f"Steps: {len(result['steps'])}")
    for step in result['steps']:
        print(f"  {step['step']}. {step['action']}: {step['desc']}")
