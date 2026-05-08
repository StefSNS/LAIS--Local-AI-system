---
name: system-diagnostic
description: Monitor system health and auto-resolve issues across all interfaces
---

# Proactive System Diagnostician

## Overview
Monitors system health and auto-resolves issues across all interfaces. Triggers interface-appropriate alerts based on severity.

## Usage
```
diagnose: <check specific> | full | auto
fix: <issue_description>
monitor: start | stop | status
```

## Capabilities
- Monitors CPU, RAM, disk, network across all interfaces
- Triggers interface-appropriate alerts (voice, GUI, CLI)
- Auto-executes approved fixes across any interface
- Combines debug-assist, system monitoring, and log analysis

## Alert Levels
| Level | CLI | GUI | Voice |
|-------|-----|-----|-------|
| INFO | `[INFO]` message | Blue notification | "System status normal" |
| WARNING | `[WARN]` message | Yellow panel | "Minor issue detected" |
| ERROR | `[ERR]` message | Red dialog | "Error: [description]" |
| CRITICAL | `[CRIT]` + exit | Red flash + sound | "Critical failure!" |

## Implementation
Merges:
- Omnis debug-assist skill
- Jarvis system monitoring (computer_settings.py)
- OpenCode bash/grep for log parsing

## Auto-Fix Rules
```json
{
  "high_cpu": "kill_resource_heavy_processes",
  "low_disk": "clean_temp_files",
  "memory_leak": "restart_service",
  "network_down": "reset_adapter"
}
```
