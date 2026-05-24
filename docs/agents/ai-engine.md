# AI Engine

The AI Engine is a desktop GUI orchestrator with 40+ hot-loaded plugins, RAG pipeline, and multi-agent routing.

## Features

- **Plugin System** — 40+ hot-loaded plugins with file watcher
- **Local LLM** — RAG pipeline with local inference
- **Multi-Agent Router** — Routes tasks to JARVIS or OpenCode
- **Token Manager** — Integrated token optimization pipeline
- **Session Tracking** — Active session logging and recovery
- **Knowledge Base** — RAG with vector search

## Plugin Categories

| Category | Examples |
|----------|---------|
| Communication | Telegram, WhatsApp, Email, Discord |
| Search | Web, File, Code, Image, Video |
| Automation | Scheduler, Reminder, Workflow |
| Development | Git, Docker, Debugger, Profiler |
| Analysis | Sentiment, Summarizer, Translator |
| Media | Image gen, Audio, Video processing |
| Security | Audit, Firewall, Scanner |

## Running

```bash
python models/ai_engine/main.py
```

## Headless Mode

For server deployments, use the Docker API:

```bash
docker compose up lais-api
```

## Plugin Development

Plugins are Python files dropped into `models/ai_engine/plugins/`. They are automatically loaded by the file watcher. See existing plugins for examples.
