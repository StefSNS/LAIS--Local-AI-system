---
name: plugin-extender
description: Dynamically load and share skills/plugins across all three systems
---

# Plugin Skill Extender

## Overview
Dynamically loads and shares skills/plugins across OpenCode, Omnis, and Jarvis. Converts between skill formats automatically.

## Usage
```
plugins: list | export <name> | import <name> | convert <name> --to=opencode|omnis|jarvis
```

## Capabilities
- Exports Omnis plugins as action tools for Jarvis and CLI skills for OpenCode
- Converts Jarvis action tools to Omnis plugins and OpenCode CLI skills
- Supports voice-triggered plugin installation across all interfaces
- Auto-discovers plugins/skills in all three systems

## Conversion Matrix
| From | To | Method |
|------|----|--------|
| Omnis plugin | Jarvis action | Wrap in action_*.py template |
| Omnis plugin | OpenCode skill | Create SKILL.md + implementation |
| Jarvis action | Omnis plugin | Extract to plugin/*.py |
| Jarvis action | OpenCode skill | Create SKILL.md with tool schema |
| OpenCode skill | Omnis plugin | Convert to plugin format |
| OpenCode skill | Jarvis action | Generate action_*.py |

## Implementation
Extends:
- Omnis plugin architecture (plugin_manager.py)
- Jarvis action tool registry (main.py TOOL_DECLARATIONS)
- OpenCode skill loading logic

## Registry Format
```json
{
  "plugin_name": "example",
  "source_system": "omnis",
  "target_systems": ["opencode", "jarvis"],
  "converted_on": "2026-04-28",
  "status": "active"
}
```
