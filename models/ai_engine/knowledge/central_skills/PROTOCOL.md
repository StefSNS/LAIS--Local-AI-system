# Central Skills Sync Protocol

## Overview
Unified skills system shared across OpenCode, Omnis AI, and Jarvis. Single source of truth, auto-sync on launch.

## Central Skills Registry

**Location:** `%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\central_skills\`

```
knowledge/central_skills/
├── registry.json              # Skills index with metadata
├── code-review/SKILL.md
├── test-generator/SKILL.md
├── debug-assist/SKILL.md
├── refactor/SKILL.md
├── documentation/SKILL.md
├── security-audit/SKILL.md
└── (future skills...)
```

## Agent Local Skills

| Agent | Local Skills Folder |
|-------|-------------------|
| **OpenCode** | `.opencode/skills/` |
| **Omnis** | `knowledge/skills/` |
| **Jarvis** | `skills/` (in Mark-XXXV) |

## Sync Protocol

### On Launch/Load, each agent MUST:

```
1. Read central registry: knowledge/central_skills/registry.json
2. Compare with local skills (by last_modified timestamp)
3. Copy any new/updated skills from central to local
4. Log sync result to session
```

### registry.json format:
```json
{
  "version": "1.0",
  "last_sync": "2026-04-26T16:30:00Z",
  "skills": {
    "code-review": {
      "description": "Review code for security, bugs...",
      "created": "2026-04-26",
      "updated": "2026-04-26"
    },
    "...": {}
  }
}
```

### Creating a New Skill:

```
1. Add skill to: knowledge/central_skills/<name>/SKILL.md
2. Update registry.json with new skill metadata
3. On next launch, ALL agents auto-sync
```

## Hardcoded Sync Command (manual trigger)

```
python knowledge/skills/sync_centralskills.py
```

## Implementation

Each agent includes a sync function:

```python
# In knowledge/skills/sync_centralskills.py
import json
import shutil
from pathlib import Path

CENTRAL = Path(__file__).parent / "central_skills"
LOCAL_MAP = {
    "opencode": Path("../../.opencode/skills"),
    "omnis": Path("../skills"),
    "jarvis": Path("../../Mark-XXXV/skills")
}

def sync_for(agent):
    # Read registry, copy new skills to agent's local folder
    ...
```

## Summary

- **One place to add skills**: `knowledge/central_skills/`
- **Auto-sync on launch**: All 3 agents check and update
- **Single source of truth**: No duplicate skills
- **Version controlled**: registry.json tracks changes