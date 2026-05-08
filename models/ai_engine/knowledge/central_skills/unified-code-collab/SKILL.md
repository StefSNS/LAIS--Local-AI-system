---
name: unified-code-collab
description: Synchronized code editing and review across CLI, GUI, and Voice interfaces
---

# Unified Code Collaborator

## Overview
Enables synchronized code editing and review across all interface types. Syncs changes between CLI, customtkinter GUI, and voice input streams.

## Usage
```
collab: <describe code task>
collab review <file_path>
collab sync <file_path>
```

## Capabilities
- Syncs code changes between CLI, GUI, and Voice interfaces
- Integrates code-review, code_helper, and edit/write tools
- Generates voice-optimized diff summaries for auditory readout
- Real-time collaborative editing with conflict resolution

## Commands
| Command | Action |
|---------|--------|
| `collab:` | Start collaborative code task |
| `collab review <file>` | Review code with multi-interface output |
| `collab sync <file>` | Sync changes across interfaces |
| `collab diff` | Show differences in voice-optimized format |

## Implementation
Combines:
- Omnis code-review skill (knowledge/skills/code-review/)
- Jarvis code_helper action (actions/code_helper.py)
- OpenCode edit/read/write tools

## Cross-Interface Sync
- CLI: Direct file operations via edit/read
- GUI: WebSocket sync to Omnis customtkinter widgets
- Voice: Audio diff summaries via Jarvis TTS
