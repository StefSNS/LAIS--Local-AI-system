#!/usr/bin/env python3
"""
Self-Improvement Refine Script v2.0
Runs every 24 hours to analyze and improve AI knowledge bases, skills, and memory.
Now covers: Omnis, Jarvis, OpenCode (3 agents).
On approval, implements suggested improvements automatically.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from difflib import SequenceMatcher

SCRIPT_DIR = Path(__file__).parent / ".."
KNOWLEDGE_BASE = SCRIPT_DIR / "base"
CENTRAL_SKILLS = SCRIPT_DIR / "central_skills"
MEMORY_DIR = SCRIPT_DIR / "memory"
LOG_FILE = MEMORY_DIR / "self_improve_log.json"
REGISTRY_FILE = SCRIPT_DIR / "agents_registry.json"

# All agents that use these skills
AGENTS = ["opencode", "omnis", "jarvis"]

def load_log():
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            pass
    return {"last_run": None, "runs": [], "approved_fixes": []}

def save_log(log):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(json.dumps(log, indent=2), encoding="utf-8")

def load_registry():
    """Track all agents and their skill/knowledge versions."""
    if REGISTRY_FILE.exists():
        try:
            return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            pass
    return {
        "agents": {
            "opencode": {"skills_path": ".opencode/skills", "last_sync": None},
            "omnis": {"skills_path": "knowledge/central_skills", "last_sync": None},
            "jarvis": {"skills_path": "knowledge/central_skills", "last_sync": None}
        },
        "skill_versions": {},
        "last_updated": None
    }

def save_registry(registry):
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2), encoding="utf-8")

def get_all_knowledge_files():
    """Dynamically discover all knowledge base files."""
    if not KNOWLEDGE_BASE.exists():
        return []
    return [f for f in KNOWLEDGE_BASE.iterdir() if f.suffix == ".md"]

def get_all_skills():
    """Dynamically discover all skills."""
    if not CENTRAL_SKILLS.exists():
        return []
    return [d for d in CENTRAL_SKILLS.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]

def analyze_knowledge_base():
    """Analyze knowledge base for completeness, quality, and roadmap gaps."""
    suggestions = []
    
    # Dynamically get all files
    kb_files = get_all_knowledge_files()
    existing_files = {f.name for f in kb_files}
    
    # Check for minimum content length
    for file_path in kb_files:
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = len(content.splitlines())
            
            if lines < 30:
                suggestions.append({
                    "type": "too_short",
                    "file": file_path.name,
                    "lines": lines,
                    "priority": "medium",
                    "action": f"Expand {file_path.name} - only {lines} lines"
                })
            
            # Check for roadmap coverage
            if "roadmap" in file_path.name and "##" not in content:
                suggestions.append({
                    "type": "poor_structure",
                    "file": file_path.name,
                    "priority": "low",
                    "action": f"Add section headers to {file_path.name}"
                })
                
        except Exception as e:
            suggestions.append({
                "type": "read_error",
                "file": file_path.name,
                "priority": "high",
                "action": f"Fix unreadable file: {file_path.name} - {e}"
            })
    
    # Check for missing topics based on roadmap.sh
    expected_topics = {
        "python.md": "Python best practices from roadmap",
        "git_github.md": "Git and GitHub from roadmap",
        "docker.md": "Docker from roadmap",
        "linux.md": "Linux basics from roadmap",
        "api_security.md": "API security deep-dive"
    }
    
    for filename, topic in expected_topics.items():
        if filename not in existing_files:
            suggestions.append({
                "type": "missing",
                "file": filename,
                "topic": topic,
                "priority": "medium",
                "action": f"Create {filename} ({topic})"
            })
    
    return suggestions

def analyze_skills():
    """Analyze skills for completeness, quality, and roadmap alignment."""
    suggestions = []
    
    skills = get_all_skills()
    existing_skills = {s.name for s in skills}
    
    # Check for minimum content
    for skill_dir in skills:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            suggestions.append({
                "type": "missing_skill_file",
                "skill": skill_dir.name,
                "priority": "high",
                "action": f"Create SKILL.md for {skill_dir.name}"
            })
            continue
            
        try:
            content = skill_md.read_text(encoding="utf-8")
            lines = len(content.splitlines())
            
            if lines < 30:
                suggestions.append({
                    "type": "skill_too_short",
                    "skill": skill_dir.name,
                    "lines": lines,
                    "priority": "medium",
                    "action": f"Expand {skill_dir.name} - only {lines} lines"
                })
            
            # Check for roadmap alignment
            if skill_dir.name == "api-design" and "OWASP" not in content:
                suggestions.append({
                    "type": "missing_roadmap_content",
                    "skill": skill_dir.name,
                    "priority": "high",
                    "action": f"Add OWASP API Top 10 to {skill_dir.name}"
                })
            
            if skill_dir.name == "code-review" and "PEP 8" not in content:
                suggestions.append({
                    "type": "missing_roadmap_content",
                    "skill": skill_dir.name,
                    "priority": "medium",
                    "action": f"Add PEP 8 / Python standards to {skill_dir.name}"
                })
                
        except Exception as e:
            suggestions.append({
                "type": "read_error",
                "skill": skill_dir.name,
                "priority": "high",
                "action": f"Fix unreadable SKILL.md in {skill_dir.name}: {e}"
            })
    
    # Check for missing skills based on roadmap.sh
    roadmap_skills = {
        "git-helper": "Git and GitHub roadmap",
        "docker-helper": "Docker roadmap",
        "linux-basics": "Linux roadmap",
        "prompt-engineering": "Prompt Engineering roadmap",
        "context-engineering": "AI Engineer roadmap",
        "rag-implementation": "RAG from AI roadmap"
    }
    
    for skill, topic in roadmap_skills.items():
        if skill not in existing_skills:
            suggestions.append({
                "type": "missing_skill",
                "skill": skill,
                "topic": topic,
                "priority": "low" if skill == "prompt-engineering" else "medium",
                "action": f"Create {skill} skill ({topic})"
            })
    
    return suggestions

def analyze_memory():
    """Analyze memory system for improvements."""
    suggestions = []
    
    # Check long_term.json structure
    long_term_file = MEMORY_DIR / "long_term.json"
    if long_term_file.exists():
        try:
            data = json.loads(long_term_file.read_text(encoding="utf-8"))
            # Check if identity is populated
            if not data.get("identity"):
                suggestions.append({
                    "type": "empty_memory",
                    "component": "long_term.json",
                    "priority": "high",
                    "action": "Populate identity section in long_term.json"
                })
            if not data.get("projects"):
                suggestions.append({
                    "type": "empty_memory",
                    "component": "long_term.json",
                    "priority": "medium",
                    "action": "Populate projects section in long_term.json"
                })
        except Exception as e:
            suggestions.append({
                "type": "corrupt_memory",
                "component": "long_term.json",
                "priority": "high",
                "action": "Fix corrupted long_term.json"
            })
    
    # Check crystallized knowledge
    crystal_file = MEMORY_DIR / "crystallized_knowledge.json"
    if crystal_file.exists():
        try:
            data = json.loads(crystal_file.read_text(encoding="utf-8"))
            if len(data) < 5:
                suggestions.append({
                    "type": "sparse_crystallized",
                    "component": "crystallized_knowledge.json",
                    "count": len(data),
                    "priority": "medium",
                    "action": f"Add more crystallized learnings (currently {len(data)})"
                })
        except Exception as e:
            pass
    
    # Check session files cleanup
    sessions_dir = MEMORY_DIR / "sessions"
    if sessions_dir.exists():
        session_files = list(sessions_dir.glob("session_*.json"))
        if len(session_files) > 10:
            suggestions.append({
                "type": "too_many_sessions",
                "component": "sessions/",
                "count": len(session_files),
                "priority": "low",
                "action": f"Clean up old sessions (currently {len(session_files)} files)"
            })
    
    return suggestions

def analyze_cross_agent_sync():
    """Check if all agents have the same skills."""
    suggestions = []
    
    registry = load_registry()
    
    # Check if sync is needed
    for agent in AGENTS:
        agent_skills_dir = SCRIPT_DIR.parent / registry["agents"][agent]["skills_path"]
        if agent_skills_dir.exists():
            agent_skills = {d.name for d in agent_skills_dir.iterdir() if d.is_dir()}
            central_skills = {s.name for s in get_all_skills()}
            
            missing_in_agent = central_skills - agent_skills
            if missing_in_agent:
                suggestions.append({
                    "type": "sync_needed",
                    "agent": agent,
                    "missing": list(missing_in_agent),
                    "priority": "high",
                    "action": f"Sync {agent}: missing {missing_in_agent}"
                })
    
    return suggestions

def run_analysis():
    """Run full analysis across all components."""
    print(f"[{datetime.now()}] Running self-improvement analysis v2.0...")
    print("=" * 60)
    
    kb_suggestions = analyze_knowledge_base()
    skill_suggestions = analyze_skills()
    memory_suggestions = analyze_memory()
    sync_suggestions = analyze_cross_agent_sync()
    
    all_suggestions = (
        kb_suggestions + skill_suggestions + 
        memory_suggestions + sync_suggestions
    )
    
    return all_suggestions

def log_run(suggestions):
    """Log the analysis run."""
    log = load_log()
    log["last_run"] = datetime.now(timezone.utc).isoformat()
    log["runs"].append({
        "timestamp": log["last_run"],
        "total_suggestions": len(suggestions),
        "by_type": {
            "knowledge_base": len([s for s in suggestions if "file" in s]),
            "skills": len([s for s in suggestions if "skill" in s]),
            "memory": len([s for s in suggestions if "component" in s]),
            "sync": len([s for s in suggestions if "agent" in s])
        },
        "suggestion_list": suggestions[:10]  # First 10 for reference
    })
    log["runs"] = log["runs"][-20:]  # Keep last 20 runs
    save_log(log)

def auto_fix(suggestions):
    """Automatically fix approved suggestions."""
    fixed = []
    
    for s in suggestions:
        if s.get("type") == "sync_needed" and s.get("priority") == "high":
            # Trigger sync
            sync_script = SCRIPT_DIR / "sync_centralskills.py"
            if sync_script.exists():
                try:
                    import subprocess
                    result = subprocess.run(
                        ["python", str(sync_script), "sync", "all"],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0:
                        fixed.append(f"Synced all agents: {s['agent']}")
                except Exception as e:
                    pass
    
    return fixed

def main():
    print("=" * 60)
    print("AI Self-Improvement Refine Script v2.0")
    print("Analyzing: Omnis, Jarvis, OpenCode")
    print("=" * 60)
    
    suggestions = run_analysis()
    
    if not suggestions:
        print("\n✓ No improvements needed at this time.")
        log_run(suggestions)
        return
    
    print(f"\nFound {len(suggestions)} suggestions:\n")
    
    # Group by priority
    high = [s for s in suggestions if s.get("priority") == "high"]
    medium = [s for s in suggestions if s.get("priority") == "medium"]
    low = [s for s in suggestions if s.get("priority") == "low"]
    
    for priority, items in [("HIGH", high), ("MEDIUM", medium), ("LOW", low)]:
        if items:
            print(f"\n[{priority}] ({len(items)} items):")
            for i, s in enumerate(items, 1):
                action = s.get("action", s.get("topic", s.get("skill", "Unknown")))
                print(f"  {i}. {action}")
    
    print("\n" + "=" * 60)
    print("Auto-fixing high priority sync issues...")
    fixed = auto_fix(suggestions)
    if fixed:
        print("Fixed:")
        for f in fixed:
            print(f"  ✓ {f}")
    
    print("\nTo manually approve other improvements:")
    print("  1. Review suggestions above")
    print("  2. Edit knowledge/skills as needed")
    print("  3. Run sync: python sync_centralskills.py sync all")
    print("=" * 60)
    
    log_run(suggestions)

if __name__ == "__main__":
    main()
