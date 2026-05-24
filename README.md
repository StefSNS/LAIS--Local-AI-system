<p align="center">
  <img src=".github/banner.png" alt="LAIS Banner" width="600"/>
</p>

<h1 align="center">LAIS — Local AI System</h1>

<p align="center">
  <strong>Three autonomous agents. One shared brain. Zero cloud dependency.</strong>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python 3.11+"></a>
  <a href="#"><img src="https://img.shields.io/badge/Platform-Windows_10%2F11-blue" alt="Windows"></a>
  <a href="#"><img src="https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/Agents-3-brightgreen" alt="3 Agents"></a>
  <a href="#"><img src="https://img.shields.io/badge/Plugins-40%2B-orange" alt="40+ Plugins"></a>
  <a href="#"><img src="https://img.shields.io/badge/Skills-30%2B-yellow" alt="30+ Skills"></a>
  <a href="#"><img src="https://img.shields.io/badge/Memory_Architecture-v3.0-purple" alt="Memory v3"></a>
</p>

---

## What is LAIS?

LAIS is a **multi-agent AI operating system** that runs three autonomous agents simultaneously on your local machine:

| Agent | Interface | Purpose |
|-------|-----------|---------|
| **JARVIS** (Mark XXXIX) | Voice + Vision | Real-time voice AI via Gemini Live, screen/webcam analysis, desktop control, security grid |
| **AI Engine** | Desktop GUI | Plugin orchestrator with 40+ hot-loaded plugins, RAG pipeline, local LLM inference, multi-agent routing |
| **OpenCode** | CLI Terminal | 30+ coding skills: TDD, refactoring, code review, research, debugging |

All three agents share a **unified memory layer** — JARVIS remembers what OpenCode did, AI Engine orchestrates complex multi-step workflows, and OpenCode handles precise code operations. They communicate through the **CoComm cross-agent protocol** with A2A server, WebSocket messaging, shared memory, trust scoring, and consensus.

---

## What Makes LAIS Unique

While projects like **OpenClaw** (374K stars), **Hermes Agent** (140K stars), and **AutoGPT** (150K stars) have pioneered the AI agent space, LAIS occupies a distinct architectural niche:

### 1. Triple-Agent Architecture
No other open-source system runs **voice AI + GUI orchestrator + CLI coder** simultaneously with shared memory. OpenClaw is messaging-first. Hermes is CLI-only. LAIS has all three modalities in one system.

### 2. 4-Layer Memory Architecture (v3.0)
```
Hot (100%)   → Full context, current session
Warm (60%)   → Summarized recent interactions
Cold (20%)   → Metadata only, full compression
Crystallized (90%) → Key learnings, permanent storage
```
Neither OpenClaw nor Hermes tiers memory by compression level with graduated retention.

### 3. Token Optimization Pipeline (v1.0.0)
Four compression engines in a single pipeline with per-agent USD budgeting:
- **claw-compactor** — 14-stage content-type-aware compression
- **LLMLingua** — Microsoft 20x semantic compression
- **tokenpruner** — 40-60% dedup compression (COMPOSITE strategy)
- **shekel** — Per-agent USD budget enforcement (warn at 80%, stop at 100%)
- **ResponseCache** — TTL-based response deduplication

### 4. 9-Agent Security Grid
Dedicated security sub-agents built into JARVIS:
`network_shield` · `code_sentry` · `file_watchdog` · `input_sanitizer` · `auth_gate` · `anomaly_detector` · `crypto_guard` · `audit_logger` · `decoy_engine`

### 5. CoComm Cross-Agent Protocol (16 Modules)
| Module | Purpose | Module | Purpose |
|--------|---------|--------|---------|
| A2A Server | Agent-to-agent task delegation | Session Log | Active session tracking |
| WebSocket | Real-time messaging | Shared Memory | Cross-agent memory store |
| MCP Bridge | Model Context Protocol | Config | Configuration management |
| Vault Sync | Knowledge base sync | Roles | Agent role definitions |
| Trigger | Event-driven triggers | Handoff | Task handoff protocols |
| Async Agent | Async execution | Goal Planner | Multi-agent planning |
| Consensus | Decision consensus | Graph Evolution | Dynamic knowledge graph |
| Trust | Trust scoring/validation | Memory Sync | Memory synchronization |

### 6. Knowledge Vault Integration
LAIS uses an **Obsidian vault** as its source of truth — all shared memory, protocols, agent registries, and crystallized learnings live in a structured, queryable knowledge base. Bi-directional sync means the vault updates from agent activity and agents query the vault for context.

### 7. Windows Native
While OpenClaw and Hermes target Linux/Mac, LAIS is **born on Windows 11** with PowerShell-native automation, Windows Task Scheduler integration, and native Windows desktop control.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         LAIS SYSTEM                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │   JARVIS (Voice) │  │   AI Engine (GUI)│  │ OpenCode (CLI) │ │
│  │   Mark XXXIX     │  │   40+ Plugins    │  │   30+ Skills   │ │
│  │   Gemini Live    │  │   RAG Pipeline   │  │   Code Ops     │ │
│  │   Screen Vision  │  │   Local LLM      │  │   Refactoring  │ │
│  │   Desktop Ctrl   │  │   Orchestrator   │  │   TDD/Review   │ │
│  │   Security Grid  │  │   Self-Improve   │  │   Research     │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬────────┘ │
│           │                     │                     │          │
│           └─────────────────────┼─────────────────────┘          │
│                                 │                                 │
│                    ┌────────────┴────────────┐                   │
│                    │     UNIFIED LAYER       │                   │
│                    │  Memory · Routing · Sync │                   │
│                    │  Token Optimization     │                   │
│                    │  60 Integration Modules │                   │
│                    └────────────┬────────────┘                   │
│                                 │                                 │
│                    ┌────────────┴────────────┐                   │
│                    │       KNOWLEDGE         │                   │
│                    │   Obsidian Vault Sync   │                   │
│                    │   Crystallized Memory   │                   │
│                    │   RAG · SQLite FTS5     │                   │
│                    └─────────────────────────┘                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- **Windows 10/11** (primary target; Linux/Mac via WSL2)
- **Python 3.11+**
- **~2GB free disk space** (source code only; models require additional)

### One-Line Install
```powershell
powershell -c "irm https://raw.githubusercontent.com/StefSNS/LAIS/main/install.ps1 | iex"
```

### Or via pip
```bash
pip install lais-ai
lais install
```

### Manual Install
```bash
git clone https://github.com/StefSNS/LAIS.git
cd LAIS
python install.py
```

### Start All Agents
```powershell
.\launch\start_all.ps1

# Or individually:
python models\Mark-XXXIX\main.py      # JARVIS voice AI
python models\ai_engine\main.py       # AI Engine GUI
lais_opencode.py                      # OpenCode launcher
```

---

## Use Cases

| Scenario | How LAIS Handles It |
|----------|-------------------|
| **"Research quantum computing and build a demo"** | AI Engine RAG-searches knowledge base → drafts report → delegates code to OpenCode |
| **"What's on my screen? Open that file."** | JARVIS captures screen via Gemini Vision → identifies file → opens it |
| **"Review and refactor this module"** | OpenCode runs code review skill → applies refactoring → JARVIS announces completion |
| **"Set a reminder for my 3pm meeting"** | JARVIS captures voice → schedules Windows task → confirmation spoken |
| **"Find that email about the API key from last week"** | AI Engine semantic search across memory + email plugin → returns result |
| **"Monitor my system health"** | JARVIS security grid runs diagnostics → AI Engine logs to vault → OpenCode creates report |

---

## Comparison with Other AI Systems

| Feature | LAIS | OpenClaw | Hermes Agent | AutoGPT |
|---------|------|----------|-------------|---------|
| **Voice AI** | Native (Gemini Live) | No | No | No |
| **Desktop GUI** | CustomTkinter | Web UI only | No | No |
| **CLI Agent** | OpenCode skills | Built-in | Built-in | Built-in |
| **Triple Interface** | Voice + GUI + CLI | Messaging only | CLI only | CLI only |
| **Tiered Memory** | 4-layer (v3.0) | Flat persistence | Persistent files | Flat |
| **Token Optimization** | 4-engine pipeline | None | None | None |
| **Security Grid** | 9 dedicated agents | Prompt guard | None | None |
| **Cross-Agent Protocol** | 16-module CoComm | None | None | None |
| **Knowledge Vault** | Obsidian sync | None | None | None |
| **Per-Agent Budgeting** | shekel enforcement | None | None | None |
| **Self-Improving Skills** | Manual | Auto (Hermes) | Auto | Limited |
| **Messaging Platforms** | None | 14+ providers | 14+ providers | None |
| **Windows Native** | Yes | Secondary | WSL2 | Secondary |
| **GitHub Stars** | New | 374K | 140K | 150K |

---

## Directory Structure

```
LAIS/
├── install.py                     # Bootstrap installer
├── lais_opencode.py               # OpenCode launcher
├── auto_loader.py                 # Session start protocol
├── README.md                      # This file
├── LICENSE
├── models/
│   ├── Mark-XXXIX/                # JARVIS voice AI
│   │   ├── main.py                # Entry point (PyQt6 + Gemini Live)
│   │   ├── ui.py                  # Desktop UI
│   │   ├── actions/               # 17 action modules
│   │   │   ├── browser_control.py
│   │   │   ├── desktop.py
│   │   │   ├── screen_processor.py
│   │   │   ├── send_message.py
│   │   │   ├── web_search.py
│   │   │   └── ... (17 total)
│   │   ├── agency/                # Security agency (9 agents)
│   │   ├── core/                  # System prompt
│   │   ├── memory/                # Memory manager
│   │   └── config/                # API key template
│   └── ai_engine/                 # AI Engine orchestrator
│       ├── main.py                # CustomTkinter GUI
│       ├── llm_engine.py          # LLM inference gateway
│       ├── plugin_manager.py      # Hot-loads 40+ plugins
│       ├── plugins/               # Plugin modules
│       ├── unified_layer/         # 60 integration modules
│       │   ├── token_optimizer.py
│       │   ├── memory_sync.py
│       │   ├── skill_engine.py
│       │   ├── rag_pipeline.py
│       │   ├── orchestrator.py
│       │   ├── a2a_server.py
│       │   └── ... (60 total)
│       ├── knowledge/             # RAG, memory, skills
│       ├── mcp_servers/           # MCP servers
│       └── local_llm/             # Local LLM scripts
├── config/
│   └── system.json                # Shared configuration
├── launch/
│   └── start_all.ps1              # Launch all agents
├── addons/
│   └── token-optimizer/           # Token optimization v1.0.0
└── integrations/                  # External tool configs
```

---

## Token Optimization Layer

```
LLM Call → CompressionPipeline → claw-compactor + tokenpruner → Compressed Prompt → LLM
                    ↓
Shell Command → ShellCompressor → sqz compressor → Compressed Output → LLM
                    ↓
Any LLM Call → TokenBudget → shekel cost tracking → Block if over budget
                    ↓
All operations → Token Log → Usage stats & reporting
```

```python
from unified_layer.token_optimizer import get_token_optimizer

opt = get_token_optimizer("jarvis")
opt.get_report()  # Full token usage + savings report
```

**Environment variables:** `LAIS_TOKEN_OPTIMIZATION=1`, `LAIS_SQZ_ENABLED=1`, `LAIS_BUDGET_ENABLED=1`

---

## Community & Roadmap

### v2.0 — Current Release
- [x] Three-agent architecture (JARVIS + AI Engine + OpenCode)
- [x] 60 unified_layer integration modules
- [x] Token Optimization v1.0.0 pipeline
- [x] Memory Architecture v3.0 (4-layer)
- [x] CoComm 16-module cross-agent protocol
- [x] JARVIS Mark XXXIX with Gemini Live voice
- [x] 9-agent security grid
- [x] Obsidian vault sync

### v2.1 — Coming Soon
- [ ] Messaging gateway (Telegram, Discord, WhatsApp)
- [ ] One-line pip install (`pip install lais-ai`)
- [ ] Docker deployment
- [ ] Linux native support
- [ ] Self-improving skills engine
- [ ] Model marketplace

### v3.0 — Vision
- [ ] Agent social network (MoltBook-style)
- [ ] Community skill marketplace
- [ ] Web UI dashboard
- [ ] Mobile companion app
- [ ] Plugin SDK for third-party developers

---

## License

**CC BY-NC 4.0** — Personal and non-commercial use only. Commercial licenses available upon request.

## Security

This system has full access to your computer. Review [SECURITY.md](SECURITY.md) before deployment. JARVIS includes a 9-agent security grid for defense-in-depth, but ultimate responsibility rests with the user.

---

<p align="center">
  <sub>Built with Python, CustomTkinter, PyQt6, Gemini Live API, and way too much coffee.</sub><br/>
  <sub>LAIS — <a href="https://github.com/StefSNS/LAIS">GitHub</a></sub>
</p>
