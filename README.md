# MARK XXXV — Personal AI Assistant

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows_10%2F11-blue)](https://www.microsoft.com/windows)

> **A real-time, voice-driven personal AI assistant for your desktop.**
> Speak to it like J.A.R.V.I.S. — it listens, responds, controls your computer, searches the web, manages files, runs code, and remembers what matters to you.

---

## Features

| Capability | Description |
|---|---|
| 🎤 **Real-Time Voice** | Speak naturally, get spoken responses via Gemini Live API streaming audio |
| 👁️ **Screen Vision** | Captures and analyzes screen/webcam via Gemini Vision |
| 🖥️ **Desktop Control** | Open apps, manage files, run commands, control volume/brightness |
| 🖱️ **GUI Automation** | Click, type, scroll, find elements on screen via PyAutoGUI |
| 🌐 **Web Search** | Google + DuckDuckGo fallback, comparison mode |
| 🧠 **Persistent Memory** | Remembers your name, preferences, projects, relationships across sessions |
| 📱 **Messaging** | Send WhatsApp / Telegram messages hands-free |
| ⏰ **Reminders** | Windows Task Scheduler integration |
| 🎮 **Game Management** | Steam & Epic Games install/update/list/schedule |
| 🎵 **YouTube Control** | Play, summarize, trending, video info |
| ✈️ **Flight Search** | Google Flights integration |
| 🔧 **Code Assistant** | Write, edit, run, explain code autonomously |
| 🏗️ **Dev Agent** | Build complete multi-file projects from scratch |
| 🛡️ **Security Grid** | 9-agent adaptive defense system with randomized countermeasures |
| 📊 **System Diagnostics** | CPU, memory, disk, network health monitoring |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    MAIN.PY                           │
│         Gemini Live API Session Manager              │
│         Tool Dispatch & Orchestration                │
├─────────────────────────────────────────────────────┤
│                       │                              │
│         ┌─────────────┴─────────────┐               │
│         ▼                           ▼               │
│  ┌──────────┐               ┌──────────┐            │
│  │  ACTIONS │               │  AGENTS  │            │
│  │  ─────── │               │  ─────── │            │
│  │  • open_app              │  • planner│            │
│  │  • web_search            │  • executor            │
│  │  • file_controller       │  • error_handler       │
│  │  • cmd_control           │  • task_queue          │
│  │  • browser_control       │  • SECURITY (9 agents) │
│  │  • computer_control      └──────────┘            │
│  │  • code_helper                                     │
│  │  • dev_agent              ┌──────────┐            │
│  │  • send_message           │  MEMORY  │            │
│  │  • +10 more...            │  ─────── │            │
│  └──────────┘               │  • manager             │
│                              │  • config             │
│                              └──────────┘            │
├─────────────────────────────────────────────────────┤
│                    UI.PY                              │
│            Animated Tkinter Interface                 │
│         Status: LISTENING / SPEAKING / THINKING      │
└─────────────────────────────────────────────────────┘
```

### How It Works

1. **Voice Input** → Microphone stream sent to Gemini Live API
2. **AI Processing** → Gemini decides which tool to call based on context
3. **Tool Execution** → Python module performs the action (search, file, command, etc.)
4. **Voice Output** → Response streamed back as audio
5. **Memory Update** → Personal facts extracted and saved asynchronously

### Security Grid (Optional)

When threats are detected, the assistant can deploy up to **9 specialized defense sub-agents**:

| Agent | Target |
|---|---|
| `network_shield` | SSRF, MITM, unauthorized egress |
| `code_sentry` | RCE, eval/exec abuse, unsafe imports |
| `file_watchdog` | Path traversal, sensitive system files |
| `input_sanitizer` | SQLi, XSS, command injection |
| `auth_gate` | Rate limiting, brute force protection |
| `anomaly_detector` | Behavioral patterns, escalation chains |
| `crypto_guard` | Key validation, secret redaction |
| `audit_logger` | Integrity-protected security event logging |
| `decoy_engine` | Honeypots, fake credentials, misdirection |

Each agent deploys **randomized defenses** that rotate in real time when the attacker adapts. [Learn more](SECURITY.md).

---

## Quick Start

### Prerequisites

- **Windows 10 or 11** (primary platform)
- **Python 3.11 or 3.12** ([download](https://www.python.org/downloads/))
- **Google Gemini API key** ([get one free](https://aistudio.google.com/apikey))
- **~5GB free disk space** (models + dependencies)

### One-Step Install (Recommended)

```powershell
pip install localclaw
```

Or run the bootstrap installer directly:

```powershell
python install.py
```

> This will (automatically):
> 1. ✅ Clone MARK XXXV (voice AI), OpenCode (CLI agent), and build the AI Engine
> 2. ✅ Install all Python dependencies + Playwright browser automation
> 3. ✅ Create an Obsidian **"Shared Brain"** vault with full folder structure
> 4. ✅ Install coding language templates (Python, JS/TS, Rust, Go, Shell, SQL)
> 5. ✅ Build a skills registry from all system components
> 6. ✅ Create unified integration config linking all agents together
> 7. ✅ Generate launch scripts, user guides, and prompt templates
> 8. ✅ Run validation tests to verify everything works
> 9. ✅ Download Obsidian and create desktop shortcut

### Manual Install

```powershell
# 1. Clone the repository
git clone https://github.com/JARVIS-Systems/Mark-XXXV.git
cd Mark-XXXV

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install browser automation
playwright install chromium

# 4. Set up your API key
# Create a .env file in the project root with:
# GEMINI_API_KEY=your_key_here

# 5. Run the assistant
python main.py
```

### First Launch

1. On first launch, a UI prompt will ask for your **Gemini API key**
2. The assistant will connect and say **"At your service, sir."**
3. Start with: *"What can you do?"* or *"Introduce yourself"*

---

## What Makes This Different

| Feature | MARK XXXV | ChatGPT Desktop | Alexa/Siri | Copilot |
|---|---|---|---|---|
| **Real-time voice streaming** | ✅ Full duplex | ❌ Turn-based | ✅ | ❌ |
| **Screen/webcam vision** | ✅ Gemini Vision | ❌ | ❌ | ❌ |
| **Full computer control** | ✅ Mouse, keyboard, apps, files | ❌ | ❌ | ❌ |
| **Offline models** | ✅ GGUF (Qwen, RWKV, SmolLM) | ❌ | ❌ | ❌ |
| **Autonomous agent** | ✅ Plan + Execute + Error recovery | ❌ | ❌ | ❌ |
| **Persistent memory** | ✅ Extracts facts automatically | ❌ | ❌ | ❌ |
| **Self-healing diagnostics** | ✅ System health + auto-repair | ❌ | ❌ | ❌ |
| **Active security grid** | ✅ 9-agent adaptive defense | ❌ | ❌ | ❌ |
| **Game management** | ✅ Steam + Epic Games | ❌ | ❌ | ❌ |
| **Open source** | ✅ CC BY-NC 4.0 | ❌ | ❌ | ❌ |

---

## Ecosystem: Repos, Skills & Plugins

### Core Repositories

| Repository | Purpose |
|---|---|
| [Mark-XXXV](https://github.com/JARVIS-Systems/Mark-XXXV) | Voice-driven personal AI assistant |
| [OpenCode](https://github.com/anomalyco/opencode) | Local CLI coding agent (skills-based) |
| [AI Engine](models/ai_engine/) | Local LLM inference + Gemini API orchestration |
| [Obsidian](https://obsidian.md) | Knowledge management (the "Shared Brain") |

### Skills & Plugins by Component

| Component | Skills Location | Count |
|-----------|---------------|-------|
| **JARVIS** | `agent/planner.py`, `agent/executor.py`, `agent/security/` | 9 security sub-agents + planner/executor |
| **OpenCode** | `models/opencode/skills/` | 30+ skill files (installer auto-discovers) |
| **AI Engine** | `models/ai_engine/plugins/` | 15+ plugins (search, memory, analytics, etc.) |
| **Shared Vault** | `010_AGENTS/Skills/` | User-defined skills registry |

### Recommended Obsidian Plugins

| Plugin | Purpose |
|---|---|
| [Obsidian Git](https://github.com/denolehov/obsidian-git) | Auto-backup vault to GitHub |
| [Dataview](https://github.com/blacksmithgu/obsidian-dataview) | Query and aggregate notes like a database |
| [Templater](https://github.com/SilentVoid13/Templater) | Advanced templates with variables and JS |
| [Kanban](https://github.com/mgmeyers/obsidian-kanban) | Visual project management boards |
| [Calendar](https://github.com/liamcain/obsidian-calendar-plugin) | Daily note calendar view |
| [Tasks](https://github.com/obsidian-tasks-group/obsidian-tasks) | Full task management with dates |

### Suggested Add-Ons

| Tool | Link | Why |
|---|---|---|
| **Ollama** | https://ollama.ai | Run additional local models with simple API |
| **LM Studio** | https://lmstudio.ai | GUI for browsing/testing GGUF models |
| **Docker Desktop** | https://docker.com | Containerized dev environments |
| **Windows Terminal** | Microsoft Store | Better terminal for PowerShell/WSL |
| **GitHub Desktop** | https://desktop.github.com | GUI git client for managing repos |

---

## First Things to Try

Once running, try these commands to see what it can do:

```text
"What's on my screen?"
"Open Chrome and search for the weather today"
"Check my disk space"
"Remember that my favorite color is blue"
"Set a reminder for 30 minutes"
"Search for flights from New York to London next Friday"
"What's the latest news in technology?"
"Play the top trending video on YouTube"
"Send a message to John on WhatsApp saying I'm on my way"
"Install the game Cyberpunk 2077 from Steam"
"Run a full system diagnostic"
```

---

## User Guide

See [QUICK_START.md](QUICK_START.md) for detailed setup instructions, personalization steps, and troubleshooting.

See [USER_GUIDE.md](USER_GUIDE.md) for complete command reference, workflow guide, and advanced usage.

See [SECURITY.md](SECURITY.md) for security considerations and recommended mitigations.

---

## Requirements

- **OS:** Windows 10/11 (primary), partial macOS/Linux
- **Python:** 3.11 or 3.12
- **RAM:** 8GB minimum (16GB recommended)
- **Storage:** 5GB free
- **Microphone:** Required for voice interaction
- **Internet:** Required for Gemini API (offline models available as fallback)

---

## License

This project is licensed under **Creative Commons Attribution-NonCommercial 4.0** — see [LICENSE](LICENSE) for details.

**Personal and non-commercial use only.** You are free to share and adapt the material for non-commercial purposes with appropriate attribution.

---

## Security

⚠️ **This assistant has full access to your computer.** It can read/write files, execute commands, browse the web, and run AI-generated code. Please review [SECURITY.md](SECURITY.md) for important security considerations before deployment.

---

## Acknowledgements

- Built with [Google Gemini API](https://deepmind.google/technologies/gemini/)
- Local inference via [llama.cpp](https://github.com/ggml-org/llama.cpp)
- GGUF models from [Hugging Face](https://huggingface.co/)
- Original concept by FatihMakes
