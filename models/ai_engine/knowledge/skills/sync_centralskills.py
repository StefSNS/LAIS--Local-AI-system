import json
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).parent
CENTRAL = SCRIPT_DIR.parent / "central_skills"

# Jarvis path: env var override, or relative path from project structure
_JARVIS_PATH = os.environ.get("JARVIS_PATH", str(SCRIPT_DIR.parent.parent.parent / "Mark-XXXV"))
LOCAL_MAP = {
    "opencode": SCRIPT_DIR.parent / ".opencode" / "skills",
    "lais": SCRIPT_DIR.parent / "knowledge" / "skills",
    "jarvis": Path(_JARVIS_PATH) / "skills"
}

REGISTRY_FILE = CENTRAL / "registry.json"

def load_registry():
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    return {"version": "1.0", "last_sync": None, "skills": {}}

def save_registry(reg):
    reg["last_sync"] = datetime.now(timezone.utc).isoformat()
    REGISTRY_FILE.write_text(json.dumps(reg, indent=2), encoding="utf-8")

def sync_for(agent):
    local_dir = LOCAL_MAP.get(agent.lower())
    if not local_dir:
        print(f"Unknown agent: {agent}")
        return False
    
    if not CENTRAL.exists():
        print(f"Central skills not found: {CENTRAL}")
        return False
    
    local_dir.mkdir(parents=True, exist_ok=True)
    registry = load_registry()
    synced = []
    
    for skill_dir in CENTRAL.iterdir():
        if not skill_dir.is_dir() or skill_dir.name in ["registry.json"]:
            continue
        
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        
        local_skill = local_dir / skill_dir.name
        local_skill.mkdir(parents=True, exist_ok=True)
        
        need_update = True
        if local_skill.exists():
            local_skill_file = local_skill / "SKILL.md"
            if local_skill_file.exists():
                local_mtime = local_skill_file.stat().st_mtime
                central_mtime = skill_file.stat().st_mtime
                if local_mtime >= central_mtime:
                    need_update = False
        
        if need_update:
            dest_skill = local_skill / "SKILL.md"
            shutil.copy2(skill_file, dest_skill)
            synced.append(skill_dir.name)
    
    if synced:
        print(f"[{agent}] Synced: {', '.join(synced)}")
    else:
        print(f"[{agent}] Already up to date")
    
    save_registry(registry)
    return True

def add_skill(name, description):
    skill_dir = CENTRAL / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    content = f"""---
name: {name}
description: {description}
---

# {name.replace('-', ' ').title()} Skill

[Add instructions for this skill]
"""
    
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    
    registry = load_registry()
    registry["skills"][name] = {
        "description": description,
        "created": datetime.now(timezone.utc).isoformat()[:10],
        "updated": datetime.now(timezone.utc).isoformat()[:10]
    }
    save_registry(registry)
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: sync_centralskills.py <command>")
        print("Commands:")
        print("  sync <agent>    - Sync skills for agent (opencode|omnis|jarvis|all)")
        print("  add <name> <description> - Add new skill to central")
        print("  list          - List central skills")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "list":
        reg = load_registry()
        print("Central Skills:")
        for name, info in reg.get("skills", {}).items():
            print(f"  - {name}: {info.get('description', '')}")
        return
    
    if cmd == "sync":
        if len(sys.argv) < 3:
            print("Usage: sync_centralskills.py sync <agent>")
            return
        
        agent = sys.argv[2]
        if agent == "all":
            for a in LOCAL_MAP.keys():
                sync_for(a)
        else:
            sync_for(agent)
        return
    
    if cmd == "add":
        if len(sys.argv) < 4:
            print("Usage: sync_centralskills.py add <name> <description>")
            return
        
        add_skill(sys.argv[2], sys.argv[3])
        print(f"Added skill: {sys.argv[2]}")
        return
    
    print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()