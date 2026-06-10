> **⚠️ ARCHIVED — 2026-06-10**
>
> This repository is **outdated and no longer actively maintained**.
>
> **What changed:** LAIS has evolved substantially. The current system includes CSI-Fusion (WiFi sensing security system), Hermes Agent (multi-platform CLI with MCP), LAIS Desktop (Electron app), and a 4-agent architecture with production deployments. None of these are reflected here.
>
> **Why archived:** The public code no longer represents the actual system. This repo is preserved as a **historical reference only**.
>
> **Status:** Read-only. No further updates, issues, or PRs will be accepted.
>
> ---

<p align="center">
  <!-- banner placeholder  -->
</p>

<h1 align="center">LAIS — Local A I System</h1>

<p align="center">
  <strong>T hree autonomous agents. One shared brain. Zer o cloud dependency.</strong>
</p>

<p align=" center">
  <a href="https://pypi.org/project/ lais-ai/"><img src="https://img.shields.io/py pi/v/lais-ai?color=blue" alt="PyPI"></a>
  <a  href="#"><img src="https://img.shields.io/ba dge/Python-3.11%2B-blue" alt="Python 3.11+">< /a>
  <a href="#"><img src="https://img.shiel ds.io/badge/Platform-Windows_10%2F11-blue" al t="Windows"></a>
  <a href="#"><img src="http s://img.shields.io/badge/License-CC_BY--NC_4. 0-lightgrey" alt="License"></a>
  <a href="#" ><img src="https://img.shields.io/badge/Agent s-3-brightgreen" alt="3 Agents"></a>
  <a hre f="#"><img src="https://img.shields.io/badge/ Plugins-Hot--Load-orange" alt="Hot-Load Plugi ns"></a>
  <a href="#"><img src="https://img. shields.io/badge/Skills-34-blue" alt="34 Skil ls"></a>
  <a href="#"><img src="https://img. shields.io/badge/Memory_Architecture-v3.0-pur ple" alt="Memory v3"></a>
</p>

---

## What  is LAIS?

LAIS is a **multi-agent AI operatin g system** that runs three autonomous agents  simultaneously on your local machine:

| Agen t | Interface | Purpose |
|-------|---------- -|---------|
| **JARVIS** (Mark XXXIX) | Voic e + Vision | Real-time voice AI via Gemini Li ve, screen/webcam analysis, desktop control,  security grid |
| **AI Engine** | Desktop GUI  | Plugin orchestrator with hot-loaded plugin  system, RAG pipeline, local LLM inference, m ulti-agent routing |
| **OpenCode** | CLI Ter minal | 30+ coding skills: TDD, refactoring,  code review, research, debugging |

All three  agents share a **unified memory layer** —  JARVIS remembers what OpenCode did, AI Engine  orchestrates complex multi-step workflows, a nd OpenCode handles precise code operations.  They communicate through the **CoComm cross-a gent protocol** with A2A server, WebSocket me ssaging, shared memory, trust scoring, and co nsensus.

---

## What Makes LAIS Unique

Whi le projects like **OpenClaw** (374K stars), * *Hermes Agent** (140K stars), and **AutoGPT**  (150K stars) have pioneered the AI agent spa ce, LAIS occupies a distinct architectural ni che:

### 1. Triple-Agent Architecture
No oth er open-source system runs **voice AI + GUI o rchestrator + CLI coder** simultaneously with  shared memory. OpenClaw is messaging-first.  Hermes is CLI-only. LAIS has all three modali ties in one system.

### 2. 4-Layer Memory Ar chitecture (v3.0)
```
Hot (100%)   → Full c ontext, current session
Warm (60%)   → Summ arized recent interactions
Cold (20%)   → M etadata only, full compression
Crystallized ( 90%) → Key learnings, permanent storage
``` 
Neither OpenClaw nor Hermes tiers memory by  compression level with graduated retention.

 ### 3. Token Optimization Pipeline (v1.0.0)
F our compression engines in a single pipeline  with per-agent USD budgeting:
- **claw-compac tor** — 14-stage content-type-aware compres sion
- **LLMLingua** — Microsoft 20x semant ic compression
- **tokenpruner** — 40-60% d edup compression (COMPOSITE strategy)
- **she kel** — Per-agent USD budget enforcement (w arn at 80%, stop at 100%)
- **ResponseCache**  — TTL-based response deduplication

### 4.  9-Agent Security Grid
Dedicated security sub -agents built into JARVIS:
`network_shield` � � `code_sentry` · `file_watchdog` · `input_ sanitizer` · `auth_gate` · `anomaly_detecto r` · `crypto_guard` · `audit_logger` · `de coy_engine`

### 5. CoComm Cross-Agent Protoc ol (16 Modules)
| Module | Purpose | Module |  Purpose |
|--------|---------|--------|----- ----|
| A2A Server | Agent-to-agent task dele gation | Session Log | Active session trackin g |
| WebSocket | Real-time messaging | Share d Memory | Cross-agent memory store |
| MCP B ridge | Model Context Protocol | Config | Con figuration management |
| Vault Sync | Knowle dge base sync | Roles | Agent role definition s |
| Trigger | Event-driven triggers | Hando ff | Task handoff protocols |
| Async Agent |  Async execution | Goal Planner | Multi-agent  planning |
| Consensus | Decision consensus  | Graph Evolution | Dynamic knowledge graph | 
| Trust | Trust scoring/validation | Memory  Sync | Memory synchronization |

### 6. Knowl edge Vault Integration
LAIS uses an **Obsidia n vault** as its source of truth — all shar ed memory, protocols, agent registries, and c rystallized learnings live in a structured, q ueryable knowledge base. Bi-directional sync  means the vault updates from agent activity a nd agents query the vault for context.

### 7 . Windows Native
While OpenClaw and Hermes ta rget Linux/Mac, LAIS is **born on Windows 11* * with PowerShell-native automation, Windows  Task Scheduler integration, and native Window s desktop control.

---

## System Architectu re

```
┌───────────� ��──────────────� ��──────────────� ��──────────────� ��─────────┐
│                          LAIS SYSTEM                               │
├────────� �──────────────� �──────────────� �──────────────� �────────────┤
│                                                                    │
│  ┌────� ��─────────────┐   ┌─────────────� �────┐  ┌──────── ────────┐ │
│  │   JA RVIS (Voice) │  │   AI Engine (GUI)│  � �� OpenCode (CLI) │ │
│  │   Mark XXX IX     │  │   40+ Plugins    │  │   3 0+ Skills   │ │
│  │   Gemini Live     │  │   RAG Pipeline   │  │   Code Op s     │ │
│  │   Screen Vision  │   │   Local LLM      │  │   Refactoring   │ │
│  │   Desktop Ctrl   │  │    Orchestrator   │  │   TDD/Review   │ � �
│  │   Security Grid  │  │   Self-I mprove   │  │   Research     │ │
│   └────────┬────� �────┘  └──────── ┬─────────┘  └──� ��────┬────────┘  │
│           │                     │                      │          │
│            └───────────� �─────────┼────� �──────────────� �─┘          │
│                                  │                                  │
│                    ┌──── ────────┴────── ──────┐                   │
� ��                    │     UNIFIED LAYER        │                   │
│                     │  Memory · Routing · Sync │                    │
│                    � ��  Token Optimization     │                    │
│                    │  60 Integr ation Modules │                   │
│                     └──────── ────┬────────── ──┘                   │
│                                  │                                  │
│                    ┌� ��───────────┴──� ��─────────┐                    │
│                    │       KN OWLEDGE         │                   │
│                     │   Obsidian Vault Sync    │                   │
│                     │   Crystallized Memory   │                    │
│                    │    RAG · SQLite FTS5     │                    │
│                    └───── ─────────────── ─────┘                   │
└� ��──────────────� ��──────────────� ��──────────────� ��──────────────� ��─────┘
```

---

## Quick Start 

### Prerequisites
- **Windows 10/11** (prim ary target; Linux/Mac via WSL2)
- **Python 3. 11+**
- **~2GB free disk space** (source code  only; models require additional)

### Instal l via pip
```bash
pip install lais-ai
python  -c "from install import main; main()"
```

## # One-Line Install (Windows)
```powershell
po wershell -c "irm https://raw.githubuserconten t.com/StefSNS/LAIS--Local-AI-system/main/inst all.ps1 | iex"
```

### Manual Install
```bas h
git clone https://github.com/StefSNS/LAIS-- Local-AI-system.git
cd LAIS--Local-AI-system
 python install.py
```

### Start All Agents
` ``powershell
.\launch\start_all.ps1

# Or ind ividually:
python models\Mark-XXXIX\main.py       # JARVIS voice AI
python models\ai_engine \main.py       # AI Engine GUI
lais_opencode. py                      # OpenCode launcher
` ``

---

## Use Cases

| Scenario | How LAIS  Handles It |
|----------|-------------------| 
| **"Research quantum computing and build a  demo"** | AI Engine RAG-searches knowledge ba se → drafts report → delegates code to Op enCode |
| **"What's on my screen? Open that  file."** | JARVIS captures screen via Gemini  Vision → identifies file → opens it |
| * *"Review and refactor this module"** | OpenCo de runs code review skill → applies refacto ring → JARVIS announces completion |
| **"S et a reminder for my 3pm meeting"** | JARVIS  captures voice → schedules Windows task →  confirmation spoken |
| **"Find that email a bout the API key from last week"** | AI Engin e semantic search across memory + email plugi n → returns result |
| **"Monitor my system  health"** | JARVIS security grid runs diagno stics → AI Engine logs to vault → OpenCod e creates report |

---

## Comparison with O ther AI Systems

| Feature | LAIS | OpenClaw  | Hermes Agent | AutoGPT |
|---------|------| ----------|-------------|---------|
| **Voice  AI** | Native (Gemini Live) | No | No | No | 
| **Desktop GUI** | CustomTkinter | Web UI o nly | No | No |
| **CLI Agent** | OpenCode sk ills | Built-in | Built-in | Built-in |
| **T riple Interface** | Voice + GUI + CLI | Messa ging only | CLI only | CLI only |
| **Tiered  Memory** | 4-layer (v3.0) | Flat persistence  | Persistent files | Flat |
| **Token Optimiz ation** | 4-engine pipeline | None | None | N one |
| **Security Grid** | 9 dedicated agent s | Prompt guard | None | None |
| **Cross-Ag ent Protocol** | 16-module CoComm | None | No ne | None |
| **Knowledge Vault** | Obsidian  sync | None | None | None |
| **Per-Agent Bud geting** | shekel enforcement | None | None |  None |
| **Self-Improving Skills** | Manual  | Auto (Hermes) | Auto | Limited |
| **Messag ing Platforms** | TG/DC/WA (gateway) | 14+ pr oviders | 14+ providers | None |
| **Windows  Native** | Yes | Secondary | WSL2 | Secondary  |
| **GitHub Stars** | New | 374K | 140K | 1 50K |

---

## Directory Structure

```
LAIS/ 
├── install.py                     # B ootstrap installer
├── lais_opencode.py                # OpenCode launcher
├──  auto_loader.py                 # Session star t protocol
├── README.md                       # This file
├── LICENSE
├─� � models/
│   ├── Mark-XXXIX/                 # JARVIS voice AI
│   │   ├─� �� main.py                # Entry point (PyQt 6 + Gemini Live)
│   │   ├── ui.py                   # Desktop UI
│   │   ├ ── actions/               # 17 action mod ules
│   │   │   ├── browser_cont rol.py
│   │   │   ├── desktop.py 
│   │   │   ├── screen_processor .py
│   │   │   ├── send_message. py
│   │   │   ├── web_search.py
 │   │   │   └── ... (17 total)
� �   │   ├── agency/                #  Security agency (9 agents)
│   │   ├─ ─ core/                  # System prompt
� �   │   ├── memory/                #  Memory manager
│   │   └── config/                 # API key template
│   └� �─ ai_engine/                 # AI Engine o rchestrator
│       ├── main.py                 # CustomTkinter GUI
│       ├� �─ llm_engine.py          # LLM inference g ateway
│       ├── plugin_manager.py       # Hot-loads plugins from directory
│        ├── plugins/               # Plugi n modules
│       ├── unified_layer/          # 60 integration modules
│       � �   ├── token_optimizer.py
│       � �   ├── memory_sync.py
│       │    ├── skill_engine.py
│       │   ├ ── rag_pipeline.py
│       │   ├─ ─ orchestrator.py
│       │   ├──  a2a_server.py
│       │   └── ...  (60 total)
│       ├── knowledge/              # RAG, memory, skills
│       ├� ��─ mcp_servers/           # MCP servers
� �       └── local_llm/             # Lo cal LLM scripts
├── config/
│   └� �─ system.json                # Shared conf iguration
├── launch/
│   └── s tart_all.ps1              # Launch all agents 
├── addons/
│   └── token-opti mizer/           # Token optimization v1.0.0
 └── integrations/                  # Ex ternal tool configs
```

---

## Token Optimi zation Layer

```
LLM Call → CompressionPip eline → claw-compactor + tokenpruner → Co mpressed Prompt → LLM
                    � ��
Shell Command → ShellCompressor → sqz  compressor → Compressed Output → LLM
                     ↓
Any LLM Call → TokenBud get → shekel cost tracking → Block if ove r budget
                    ↓
All operatio ns → Token Log → Usage stats & reporting
 ```

```python
from unified_layer.token_optim izer import get_token_optimizer

opt = get_to ken_optimizer("jarvis")
opt.get_report()  # F ull token usage + savings report
```

**Envir onment variables:** `LAIS_TOKEN_OPTIMIZATION= 1`, `LAIS_SQZ_ENABLED=1`, `LAIS_BUDGET_ENABLE D=1`

---

## Community & Roadmap

### v2.0 � �� Current Release
- [x] Three-agent architec ture (JARVIS + AI Engine + OpenCode)
- [x] 60  unified_layer integration modules
- [x] Toke n Optimization v1.0.0 pipeline
- [x] Memory A rchitecture v3.0 (4-layer)
- [x] CoComm 16-mo dule cross-agent protocol
- [x] JARVIS Mark X XXIX with Gemini Live voice
- [x] 9-agent sec urity grid
- [x] Obsidian vault sync

### v2. 1 — Current Release

- [x] Messaging gatewa y (Telegram, Discord, WhatsApp) — `pip inst all lais-ai[messaging]`
- [x] One-line pip in stall (`pip install lais-ai`)
- [ ] Docker de ployment
- [ ] Linux native support
- [ ] Sel f-improving skills engine
- [ ] Model marketp lace

### v3.0 — Vision
- [ ] Agent social  network (MoltBook-style)
- [ ] Community skil l marketplace
- [ ] Web UI dashboard
- [ ] Mo bile companion app
- [ ] Plugin SDK for third -party developers

---

## License

**CC BY-N C 4.0** — Personal and non-commercial use o nly. Commercial licenses available upon reque st.

## Security

This system has full access  to your computer. Review [SECURITY.md](SECUR ITY.md) before deployment. JARVIS includes a  9-agent security grid for defense-in-depth, b ut ultimate responsibility rests with the use r.

---

<p align="center">
  <sub>Built with  Python, CustomTkinter, PyQt6, Gemini Live AP I, and way too much coffee.</sub><br/>
  <sub >LAIS — <a href="https://github.com/StefSNS /LAIS">GitHub</a></sub>
</p>
 