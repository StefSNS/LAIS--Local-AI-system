import os
import json
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "knowledge" / "skills"

def list_skills():
    if not SKILLS_DIR.exists():
        return "No skills found."
    
    skills = []
    for item in SKILLS_DIR.iterdir():
        if item.is_dir():
            skill_file = item / "SKILL.md"
            if skill_file.exists():
                meta = _parse_skill_header(skill_file)
                skills.append({
                    "name": item.name,
                    "description": meta.get("description", "No description")
                })
    
    if not skills:
        return "No skills available."
    
    result = "Available Skills:\n\n"
    for s in skills:
        result += f"• **{s['name']}**: {s['description']}\n"
    return result

def _parse_skill_header(skill_file):
    try:
        content = skill_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                meta = {}
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip()] = v.strip()
                return meta
    except Exception as e:
        pass
    return {}

def get_skill(name):
    skill_file = SKILLS_DIR / name / "SKILL.md"
    if not skill_file.exists():
        return f"Skill '{name}' not found."
    
    try:
        content = skill_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()
        return content
    except Exception as e:
        return f"Error loading skill: {e}"

def use_skill(name):
    skill_content = get_skill(name)
    if "not found" in skill_content.lower():
        return skill_content
    return f"=== Skill: {name} ===\n\n{skill_content}"

def create_skill(name, description, instructions):
    skill_dir = SKILLS_DIR / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    content = f"""---
name: {name}
description: {description}
---

# {name.title()} Skill

{instructions}
"""
    
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(content, encoding="utf-8")
    return f"Skill '{name}' created successfully."


if __name__ == "__main__":
    print(list_skills())