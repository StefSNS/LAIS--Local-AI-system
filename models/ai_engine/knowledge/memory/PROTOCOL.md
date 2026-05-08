# Unified Memory Protocol

## Overview
Unified persistent memory combining best features from Omnis (4-tier relevance) and Jarvis (categorical storage).

## Memory Architecture

```
knowledge/memory/
├── sessions/              # Session history
├── long_term.json          # Permanent memory (categories)
├── crystallized.json      # Extracted learnings
└── memory_config.json    # Memory settings
```

## Memory Categories (from Jarvis)

| Category | Content |
|----------|---------|
| `identity` | User info (name, background) |
| `preferences` | User likes/dislikes |
| `projects` | Active projects |
| `relationships` | Friends, colleagues |
| `wishes` | Goals, wants |
| `notes` | Important info |

## Tier System (from Omnis)

| Tier | Content | Relevance |
|------|--------|----------|
| Hot | Current session, active tasks | 80+ |
| Warm | Recent learnings | 50-79 |
| Cold | Past sessions | <50 |
| Crystallized | Extracted permanent | Manual |

## Key Features

1. **Relevance Scoring** (Omnis)
   - HIGH: current, active, working, code, fix, bug
   - MEDIUM: method, approach, system, function
   - LOW: old, previous, example

2. **Categorical Storage** ( Jarvis)
   - Identity, preferences, projects, relationships, wishes, notes

3. **Session Continuity**
   - Auto-save on each message
   - Load previous on startup
   - Crystallize important info

4. **Thread-Safe** (Jarvis)
   - Lock-protected writes
   - Concurrent access support

## Usage

```python
from knowledge.memory.unified_memory import UnifiedMemory

mem = UnifiedMemory()
mem.add("identity", "name", "Stefa")
mem.add("preferences", "likes", "Python, AI")
mem.save()

# Get user preferences
prefs = mem.get_category("preferences")
```

## Sync Protocol

On launch, each agent MUST:
1. Load `knowledge/memory/long_term.json`
2. Load recent session from `knowledge/memory/sessions/`
3. Load `knowledge/memory/crystallized.json`