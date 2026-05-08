# OpenCode Knowledge Base Integration

This file tells OpenCode how to access Omnis knowledge for session continuity.

## Quick Reference

**Knowledge Base Location:** `%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\`

**Key Files:**
- `memory/continuity_manager.py` - Session continuity system
- `memory/continuity_protocol.json` - Protocol config
- `memory/crystallized_knowledge.json` - Permanent learnings
- `sessions/` - Archived session data
- `*.md` - Research documents and notes

## Usage Commands

### Load Previous Session
```
Read: knowledge/memory/continuity_manager.py
```

### Get Session Context
```
Read: knowledge/sessions/session_*.json (most recent)
```

### Access Crystallized Knowledge
```
Read: knowledge/memory/crystallized_knowledge.json
```

### Search Knowledge Base
```
Grep: "keyword" in knowledge/
```

### List Available Knowledge
```
Glob: knowledge/*.md
```

## Session Continuity Protocol

When starting a new session in this project:

1. Load `knowledge/memory/crystallized_knowledge.json` for permanent learnings
2. Load most recent `knowledge/sessions/session_*.json` 
3. Use `knowledge_retriever.py` plugin to search relevant docs
4. Check `plugins/` for available tools

## Project Context

This is the Omnis AI Assistant project with:
- Local GGUF models (Qwen2.5-1.5B, Phi-3)
- Desktop AI interface
- 16+ plugins
- Memory continuity system
- Knowledge RAG system