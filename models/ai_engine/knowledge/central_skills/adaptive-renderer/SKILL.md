---
name: adaptive-renderer
description: Dynamically format outputs to match the active user interface
---

# Adaptive Output Renderer

## Overview
Detects current interface (CLI, customtkinter GUI, voice) and adjusts output format accordingly. Persists UI state when switching between modalities.

## Usage
```
render: <content> --mode=auto|cli|gui|voice
```

## Capabilities
- Auto-detects current interface and adjusts output format
- Converts structured data to CLI tables, GUI widgets, or voice summaries
- Persists UI state when switching between modalities
- Supports markdown, tables, code blocks, and rich content

## Output Formats
| Interface | Format |
|-----------|--------|
| CLI (OpenCode) | Markdown tables, code blocks, formatted text |
| GUI (Omnis) | customtkinter widgets, colored text, panels |
| Voice (Jarvis) | Concise summaries, numbered lists, audio-optimized |

## Implementation
Extends:
- Omnis customtkinter UI framework (main.py)
- Jarvis Tkinter animated UI state logic (ui.py)
- OpenCode CLI output formatting

## State Persistence
Saves UI state to `knowledge/memory/ui_state.json`:
```json
{
  "last_interface": "cli",
  "preferred_format": "markdown",
  "voice_speed": 1.0,
  "gui_theme": "dark"
}
```
