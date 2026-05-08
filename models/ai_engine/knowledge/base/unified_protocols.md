# Unified AI Protocols - Knowledge Base

## Multi-Modal Interaction Protocol

### Overview
Unified protocol for handling CLI, GUI, and Voice interactions across OpenCode, Omnis, and Jarvis systems.

### Interface Detection
```python
def detect_interface():
    # CLI: Check for terminal environment
    # GUI: Check for display server and customtkinter availability
    # Voice: Check for microphone and audio output
    pass
```

### Cross-System Communication
- OpenCode ↔ Omnis: File-based JSON messages in `knowledge/memory/sessions/`
- Omnis ↔ Jarvis: WebSocket on port 8765
- Jarvis ↔ OpenCode: Shared memory in `knowledge/memory/long_term.json`

## Workflow Orchestration

### Workflow Definition Format
```json
{
  "id": "workflow_001",
  "name": "Example Workflow",
  "steps": [
    {
      "description": "Step description",
      "tool": "tool_name",
      "interface": "cli|gui|voice",
      "fallback": "alternative_tool"
    }
  ]
}
```

### State Management
- Active workflows: `knowledge/memory/active_workflows.json`
- Completed workflows: `knowledge/memory/workflow_history.json`
- Failed workflows: `knowledge/memory/workflow_errors.json`

## Code Collaboration Protocol

### Synchronization Strategy
1. File change detected (inotify/fsevents)
2. Change broadcast to all active interfaces
3. Conflict resolution: Last-write-wins with merge option
4. Voice summary generated for audio interfaces

### Supported Operations
- Read file (all interfaces)
- Write file (CLI: direct, GUI: dialog, Voice: confirm)
- Edit file (CLI: diff, GUI: inline, Voice: summary)
- Review code (all interfaces with formatted output)

## System Diagnostics Protocol

### Health Check Intervals
- CPU/Memory: Every 30 seconds
- Disk: Every 5 minutes
- Network: Every 2 minutes
- Logs: On-demand

### Alert Thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| CPU | > 80% | > 95% |
| Memory | > 85% | > 95% |
| Disk | > 85% | > 95% |
| Network | Packet loss > 5% | Packet loss > 20% |

### Auto-Fix Actions
```json
{
  "high_cpu": ["identify_processes", "suggest_kill"],
  "low_disk": ["clean_temp", "empty_trash"],
  "memory_leak": ["restart_service", "clear_cache"],
  "network_down": ["reset_adapter", "flush_dns"]
}
```

## Asset Management Protocol

### Asset Types
- Code files: `.py`, `.js`, `.ts`, etc.
- Documentation: `.md`, `.txt`, `.pdf`
- Configuration: `.json`, `.yaml`, `.toml`
- Media: `.png`, `.jpg`, `.mp4`, etc.

### Storage Locations
- Local: Project directory
- Cache: `.knowledge/cache/`
- Cloud: Configured provider (Drive/Dropbox/OneDrive)

### Sync Strategy
1. Hash-based change detection
2. Incremental sync for large files
3. Conflict resolution: Newer version wins
4. Version history: Last 5 versions retained

## Plugin Extender Protocol

### Plugin Format Conversion
```
Omnis Plugin (.py) → Jarvis Action (action_*.py) → OpenCode Skill (SKILL.md)
```

### Registry Format
```json
{
  "plugins": [
    {
      "name": "example_plugin",
      "source": "omnis",
      "versions": {
        "opencode": "1.0",
        "omnis": "1.0",
        "jarvis": "1.0"
      },
      "last_sync": "2026-04-28T10:00:00"
    }
  ]
}
```

## Session Continuity Protocol

Based on `merged_protocol.json` (universal_session_continuity_v2.0):

### Tier Structure
- Tier 1 (Hot): Current work, full detail, 0% compression
- Tier 2 (Warm): Foundation context, 40% compression
- Tier 3 (Cold): Background info, 70% compression
- Tier 4 (Archive): Key outcomes, 85% compression
- Tier 5 (Obsolete): Pruned, 95% compression

### Auto-Classification Rules
- Relevance score > 80: Tier 1
- Relevance score 50-80: Tier 2
- Relevance score < 50: Tier 3+
- Failed/abandoned: Tier 5

### Compression Triggers
- Message count: 50 messages
- Context size: 90 docs or 6 artifacts
- Manual override: User initiated
- Session restart: Auto-compress previous

## Implementation Status (2026-04-28)
- [x] Multi-Modal Workflow skill created
- [x] Unified Code Collab skill created
- [x] Adaptive Renderer skill created
- [x] System Diagnostic skill created
- [x] Asset Manager skill created
- [x] Plugin Extender skill created
- [x] Jarvis integration complete (main.py updated with 3 new tools)
- [x] OpenCode integration complete (skills synced to .opencode/skills/)
- [x] Omnis integration complete (18 plugins available)
- [x] UI modification complete (main_cli.py created - exact OpenCode replica)

## Session Summary

### Research Phase (15 min limit)
- Audited 3 systems: Omnis (16 skills, customtkinter GUI), Jarvis (17 tools, Tkinter voice UI), OpenCode (CLI)
- Identified integration points and skill gaps

### Skills Created (6 new unified skills)
1. **multi-modal-workflow** - Cross-interface workflow orchestration
2. **unified-code-collab** - Synchronized code editing across CLI/GUI/Voice
3. **adaptive-renderer** - Dynamic output formatting per interface
4. **system-diagnostic** - Cross-system health monitoring
5. **asset-manager** - Unified file/cloud management
6. **plugin-extender** - Cross-system skill/plugin conversion

### Implementation
- **Jarvis**: Added 3 new action tools (multi_modal_workflow.py, system_diagnostic.py) + updated main.py
- **OpenCode**: Synced all 6 skills to knowledge/.opencode/skills/
- **Omnis**: Added knowledge base files, plugins already available

### UI Modification
- Created `main_cli.py` - exact OpenCode replica with:
  - `>` prompt style
  - Color-coded output (user/assistant/system/error)
  - `[tool] args` display format
  - All Omnis plugins accessible
  - Special commands: /help, /clear, /exit, /tools, /plugins
- Created `launch_cli.bat` for easy Windows launch
- Created `CLI_README.md` with full documentation
