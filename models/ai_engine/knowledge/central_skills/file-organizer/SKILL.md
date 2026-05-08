---
name: file-organizer
description: Organize project files and folder structure. Use when user asks to organize, structure, or clean up a project.
---

# File Organizer Skill

## When to Use

- User asks to "organize files", "structure project"
- User asks to "clean up folder structure"
- New project needs initial structure

## Organization Process

1. **Analyze current structure**:
   - List all files and folders
   - Identify file types and purposes
   - Note patterns in naming

2. **Plan structure**:
   - Group by type/function (src/, tests/, config/, docs/)
   - Standard locations for common files (README.md at root)
   - Consistent naming conventions

3. **Implement**:
   - Create folders
   - Move files
   - Add __init__.py where needed
   - Create placeholder files (.gitkeep, .env.example)

## Output Format

```
## Current Structure
[analysis]

## Proposed Structure
project/
├── src/
├── tests/
├── config/
├── docs/
└── ...

## Changes
1. Create src/
2. Move *.py to src/
3. ...
```

## Common Patterns

| Project Type | Structure |
|--------------|------------|
| Python lib | src/, tests/, docs/ |
| Web app | src/, public/, tests/ |
| CLI tool | src/, bin/, tests/, docs/ |
| Full-stack | client/, server/, docs/ |