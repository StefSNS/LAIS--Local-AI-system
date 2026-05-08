# LAIS — Local AI System

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows_10%2F11-blue)](https://www.microsoft.com/windows)

> **Three autonomous agents, one shared brain.**
> JARVIS (voice AI) + AI Engine (plugin orchestrator) + OpenCode (CLI coder) running simultaneously with unified memory, cross-agent task routing, and a shared knowledge vault.

---

## The Three Agents

LAIS runs three independent agents that communicate through a shared unified layer. Each is designed for a different interaction mode:

```
┌──────────────────────────────────────────────────────────┐
│                   UNIFIED LAYER                           │
│        Shared Memory · Cross-Agent Routing · Sync        │
├──────────────────────────────────────────────────────────┤
│           │                    │                         │
│    ┌──────┴──────┐    ┌──────┴──────┐    ┌─────────────┐│
│    │   JARVIS    │    │  AI ENGINE  │    │   OPENCODE   ││
│    │  (Voice AI) │    │ (Orchestr.) │    │  (CLI Agent) ││
│    ├─────────────┤    ├─────────────┤    ├─────────────┤│
│    │ Voice I/O   │    │ GUI Desktop │    │ CLI Terminal ││
│    │ Gemini Live │    │ 40+ Plugins │    │ 30+ Skills   ││
│    │ Screen Vis. │    │ RAG Pipeline│    │ File Ops     ││
│    │ Desktop Ctrl│    │ Local LLM   │    │ Code Gen     ││
│    │ Security    │    │ Multi-agent │    │ Refactoring  ││
│    │ Diagnostics │    │ Orchestrat. │    │ Code Review  ││
│    └─────────────┘    └─────────────┘    └─────────────┘│
└──────────────────────────────────────────────────────────┘
```

### How Tasks Flow Between Agents

| Trigger | Routed To | Why |
|---------|-----------|-----|
| Voice command ("open Chrome") | **JARVIS** | Fast action, low latency |
| Complex request ("research X and draft a report") | **AI Engine** | Plugin orchestration, RAG, multi-step |
| Code task ("refactor this function") | **OpenCode** | File-based operations, skill execution |
| Plugin call ("send email") | **AI Engine** | Has the email plugin |
| Security/threat detected | **JARVIS** Has the security sub-agent grid |
| Self-improvement loop | **AI Engine** | Autonomy engine, benchmarking |
| "What's in my memory about X?" | **All three** | Shared unified memory, same answer |

The **Unified Layer** (`models/ai_engine/unified_layer/`) handles cross-agent communication, memory sync, task delegation, and channel routing. Agents share the same memory store, so JARVIS remembers what OpenCode did and vice versa.

---

## Agent Capabilities

### JARVIS (Mark-XXXV) — Voice AI Assistant

- **Real-time voice** via Gemini Live API streaming audio
- **Screen vision** — captures and analyzes screen/webcam
- **Desktop control** — open apps, manage files, run commands, volume/brightness
- **GUI automation** — click, type, scroll via PyAutoGUI
- **Web search** — Google + DuckDuckGo with comparison
- **Persistent memory** — extracts facts across sessions
- **Messaging** — WhatsApp / Telegram hands-free
- **Reminders** — Windows Task Scheduler integration
- **Game management** — Steam & Epic Games
- **YouTube** — play, summarize, trending
- **Flight search** — Google Flights
- **Security Grid** — 9 adaptive defense sub-agents (network_shield, code_sentry, file_watchdog, input_sanitizer, auth_gate, anomaly_detector, crypto_guard, audit_logger, decoy_engine)
- **System diagnostics** — CPU, memory, disk, network health

### AI Engine — Plugin Orchestrator & LLM Gateway

- **Desktop GUI** — customTkinter interface with dark theme
- **40+ plugins** hot-loaded dynamically:
  - Browser automation, web scraping, semantic search
  - File management, code editing, system control
  - Email (SMTP/IMAP), reminders, cloud sync
  - Knowledge retrieval, document ingestion, research
  - Hardware detection, RAM management, screen processing
  - Task presets, intent routing, agent dispatching
  - YouTube, weather, flight finder, dictionary
- **RAG pipeline** — SQLite FTS5 search, txtai embeddings, vault curation
- **Local LLM inference** — llama.cpp server for Qwen, RWKV, SmolLM models
- **Multi-agent orchestration** — routes tasks to the right agent
- **Memory tiers** — hot (full context), warm (summarized), cold (metadata), archive (compressed)
- **Background consciousness** — runs autonomous reflection loops
- **Self-improvement engine** — benchmarks, cross-session learning
- **Unified memory** — shared across all three agents via sync layer

### OpenCode — CLI Coding Agent

- **Terminal-based** — runs in any shell, no GUI needed
- **30+ skills** loaded from skill files:
  - Brainstorming, architecture design, API design
  - Code review, debugging, testing (TDD)
  - Refactoring, documentation, migrations
  - Security audit, file organization, git workflows
  - Plan mode, multi-modal workflows, RAG implementation
- **CLI tools** — file ops, code generation, project scaffolding
- **Works alongside JARVIS and AI Engine** — tasks can be delegated to it
- **Skill registry** — auto-discovers and loads skills from `knowledge/central_skills/`

---

## What Makes This Different

| Feature | LAIS | ChatGPT Desktop | Alexa/Siri | Copilot |
|---------|------|----------------|------------|---------|
| **3 simultaneous agents** | ✅ Voice + GUI + CLI | ❌ | ❌ | ❌ |
| **Real-time voice streaming** | ✅ Full duplex | ❌ Turn-based | ✅ | ❌ |
| **Screen/webcam vision** | ✅ | ❌ | ❌ | ❌ |
| **Full computer control** | ✅ Mouse, keyboard, apps, files | ❌ | ❌ | ❌ |
| **Offline local models** | ✅ GGUF (Qwen, RWKV, SmolLM) | ❌ | ❌ | ❌ |
| **Plugin ecosystem** | ✅ 40+ hot-loaded plugins | ✅ (GPTs) | ❌ | ❌ |
| **Skill system** | ✅ 30+ skills via OpenCode | ❌ | ❌ | ❌ |
| **Cross-agent memory** | ✅ Shared unified memory | ❌ | ❌ | ❌ |
| **Autonomous agent** | ✅ Plan + Execute + Error recovery | ❌ | ❌ | ❌ |
| **Self-improvement** | ✅ Benchmarks + cross-session learning | ❌ | ❌ | ❌ |
| **Security grid** | ✅ 9-agent adaptive defense | ❌ | ❌ | ❌ |
| **Open source** | ✅ CC BY-NC 4.0 | ❌ | ❌ | ❌ |

Instead of one monolithic assistant, LAIS is **three collaborating agents** that each excel at their interaction mode. You can talk to JARVIS, watch AI Engine process complex workflows in its GUI, and invoke OpenCode for precise code operations — all sharing the same memory and context.

---

## Directory Structure

```
LAIS/
├── install.py                 # Bootstrap installer
├── README.md                  # This file
├── QUICK_START.md             # Setup guide
├── USER_GUIDE.md              # Full command reference
├── SECURITY.md                # Security considerations
├── models/
│   ├── Mark-XXXV/             # JARVIS voice AI
│   │   ├── main.py            # Entry point
│   │   ├── actions/           # 19+ action modules
│   │   ├── agent/             # Planner, executor, security
│   │   ├── memory/            # Memory manager
│   │   └── utils/             # API keys, helpers
│   ├── ai_engine/             # AI Engine orchestrator
│   │   ├── main.py            # Desktop GUI entry
│   │   ├── llm_engine.py      # LLM inference gateway
│   │   ├── plugin_manager.py  # Hot-loads 40+ plugins
│   │   ├── plugins/           # Plugin modules
│   │   ├── unified_layer/
│   │   │   ├── token_optimizer.py  # Token governance (claw, sqz, shekel, LLMLingua)
│   │   │   ├── memory_sync.py      # Cross-agent shared memory
│   │   │   └── ...                 # 40+ integration modules
│   │   ├── lais-bin/
│   │   │   └── sqz.exe        # Shell output compressor binary
│   │   ├── knowledge/         # RAG, memory, skills
│   │   └── memory_lais.py     # Shared memory backend
│   ├── llama-bin/             # llama.cpp binaries
│   └── *.gguf                 # Local LLM models
├── config/system.json         # Shared agent configuration
└── launch/start_all.ps1       # Launch all agents
```

---

## Quick Start

### Prerequisites

- **Windows 10 or 11** (primary)
- **Python 3.11 or 3.12**
- **~5GB free disk space**

### One-Step Install

```powershell
python install.py
```

This bootstraps the entire system: dependencies, plugins, skills, Obsidian vault, and integration config.

### Manual Start

```powershell
# Launch all three agents
.\launch\start_all.ps1

# Or individually:
python models\Mark-XXXV\main.py      # JARVIS voice AI
python models\ai_engine\main.py       # AI Engine GUI
# OpenCode runs from terminal (global install)
```

---

## Use Cases

| Scenario | How LAIS Handles It |
|----------|-------------------|
| **"Research quantum computing and build a demo"** | AI Engine RAG-searches knowledge base → drafts report → delegates code to OpenCode |
| **"What's on my screen? Open that file."** | JARVIS captures screen via Gemini Vision → identifies file → opens it |
| **"Review and refactor this module"** | OpenCode runs code review skill → applies refactoring → JARVIS announces completion |
| **"I need a reminder about the meeting"** | JARVIS captures voice → AI Engine schedules Windows task → confirmation spoken |
| **"Optimize my system memory"** | AI Engine's RAM manager checks model usage → unloads idle models → reports savings |
| **"Find that email about the API key from last week"** | AI Engine's semantic search across memory + email plugin → returns result |

---

---

## Token Optimization Layer

LAIS includes a cross-agent token governance system that integrates four open-source tools into a unified optimization layer:

| Tool | Integration | What It Does |
|------|-------------|-------------|
| **claw-compactor** | Prompt compression | 14-stage content-type-aware pipeline: strips markdown formatting, normalizes whitespace, deduplicates, compacts bullet lists and tables. Zero LLM inference cost. |
| **LLMLingua** (Microsoft) | Semantic compression | Uses a small BERT-level model to remove non-essential tokens while preserving meaning. Up to 20x compression. Falls back gracefully when unavailable. |
| **sqz** | Shell output compression | Rust-based CLI hook that deduplicates and compresses bash/shell/git output before it reaches the LLM. Dedup cache: identical output on repeat calls returns a 13-token reference instead of full text. |
| **shekel** | Budget enforcement | Monkey-patches OpenAI/Anthropic SDKs for per-agent USD budgets. JARVIS, AI Engine, and OpenCode each have independent budgets. Warns at 80%, stops at 100%. Loop detection prevents runaway agents. |

### Architecture

```
LLM Call → CompressionPipeline → claw-compactor + tokenpruner → Compressed Prompt → LLM
                    ↓
Shell Command → ShellCompressor → sqz binary + dedup cache → Compressed Output → LLM
                    ↓
Any LLM Call → TokenBudget → shekel cost tracking → Block if over budget
                    ↓
All operations → Token Log → Usage stats & reporting via Unified Layer
```

All 3 agents share the same optimization layer via `models/ai_engine/unified_layer/token_optimizer.py`. Shell compression is wired directly into both JARVIS and AI Engine `cmd_control` modules. Budget enforcement is available per-agent at import time.

### What Makes This Unique

**No other open-source multi-agent system combines:**
- Per-agent USD budgets with automatic enforcement
- Shell output compression with content-dedup caching
- Content-aware prompt compression (code vs JSON vs text handling differs)
- Cross-agent token usage reporting in a single dashboard
- Response caching with LRU + TTL across all agents

Enable/disable each feature via environment variables: `LAIS_TOKEN_OPTIMIZATION`, `LAIS_SQZ_ENABLED`, `LAIS_BUDGET_ENABLED` (all default `1`).

```python
from unified_layer.token_optimizer import get_token_optimizer

opt = get_token_optimizer("jarvis")
opt.get_report()  # Full token usage + savings report
```

---

## License

**CC BY-NC 4.0** — Personal and non-commercial use only. See [LICENSE](LICENSE).

## Security

⚠️ **This system has full access to your computer.** Review [SECURITY.md](SECURITY.md) before deployment.
