# Multi-Modal AI Systems Guide

## Overview
Comprehensive guide to building and integrating multi-modal AI systems that work across CLI, GUI, and Voice interfaces.

## System Comparison

### OpenCode (CLI)
- **Interface**: Command-line with markdown rendering
- **Strengths**: Fast, scriptable, low resource usage
- **Tools**: bash, read, write, edit, glob, grep, task, webfetch, websearch, codesearch
- **Best for**: Developers, automation, remote sessions

### Omnis (GUI)
- **Interface**: CustomTkinter desktop application
- **Strengths**: Visual, rich media, interactive widgets
- **Tools**: 18 plugins, RAG, multi-model support
- **Best for**: Interactive sessions, visual tasks, casual users

### Jarvis/Mark-XXXV (Voice)
- **Interface**: Tkinter with animated face, voice I/O
- **Strengths**: Hands-free, real-time, natural interaction
- **Tools**: 17 action tools, Gemini native audio
- **Best for**: Accessibility, multitasking, media control

## Integration Patterns

### Shared Memory
All systems use `knowledge/memory/long_term.json` for persistent storage.

### Cross-System Communication
```python
# OpenCode → Omnis: Write session data
# Omnis → Jarvis: WebSocket on port 8765
# Jarvis → OpenCode: Shared memory reads
```

### Unified Tool Schema
```json
{
  "name": "tool_name",
  "description": "What it does",
  "parameters": {
    "type": "OBJECT",
    "properties": {...},
    "required": [...]
  },
  "interfaces": ["cli", "gui", "voice"]
}
```

## Implementation Examples

### CLI Tool (OpenCode style)
```python
def tool_function(param1, param2):
    # Direct execution, return text/JSON
    return {"status": "success", "data": result}
```

### GUI Tool (Omnis style)
```python
def tool_function(param1, param2):
    # Update GUI widgets, return rich content
    gui.update_widget(data)
    return {"status": "success", "widget": "result_panel"}
```

### Voice Tool (Jarvis style)
```python
def tool_function(param1, param2):
    # Return audio-friendly summary
    summary = _generate_audio_summary(result)
    return {"status": "success", "summary": summary}
```

## Best Practices

1. **Interface Detection**: Auto-detect and adapt output format
2. **Graceful Degradation**: Fall back to text if GUI/Voice unavailable
3. **State Persistence**: Save state in shared memory
4. **Error Handling**: Interface-appropriate error messages
5. **Testing**: Test on all three interfaces

## Common Patterns

### Pattern: Search + Display
1. CLI: Print results as table
2. GUI: Show in scrollable list widget
3. Voice: Read top 3 results aloud

### Pattern: File Operations
1. CLI: Direct path operations
2. GUI: File dialog + drag-drop
3. Voice: "Open file named X" → file_controller

### Pattern: Code Editing
1. CLI: edit tool with diff output
2. GUI: Inline editor widget
3. Voice: "Change line 5 to..." → code_helper

## Resources
- OpenCode: / (root) - CLI tool
- Omnis: Projects/Omnis/ - GUI application
- Jarvis: Projects/LocalClaw/models/Mark-XXXV/ - Voice assistant
