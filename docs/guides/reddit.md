# Reddit Community Posts

## r/LocalLLaMA

**Title:** LAIS — triple-agent AI system: voice AI (Gemini Live) + orchestrator (40 plugins) + CLI coder, shared memory

**Body:**

I built a multi-agent AI system that runs three agents locally with a shared brain. Figured the LocalLLaMA community would appreciate the architecture.

**The architecture:**
- **JARVIS Mark XXXIX** — voice AI using Gemini Live API. Has screen vision, webcam capture, desktop control, web search, messaging (Telegram/WhatsApp), and a 9-agent security grid that validates every operation.
- **AI Engine** — desktop GUI with 40+ hot-loaded plugins (search, automation, media, dev, security). Includes a plugin watcher that hot-reloads Python files dropped into the plugins directory.
- **OpenCode** — CLI agent with 30+ coding skills: TDD (RED→GREEN→REFACTOR), code review, debugging, refactoring, research.

**Shared infrastructure:**
- **4-layer memory**: Hot (100%), Warm (60%), Cold (20%), Crystallized (90%)
- **Token optimization pipeline**: claw-compactor + LLMLingua + tokenpruner + shekel (40-60% compression)
- **18-module communication protocol**: A2A server, WebSocket, MCP bridge, shared memory, trust scoring, consensus, handoff, graph evolution
- **Messaging gateway**: Telegram + Discord + WhatsApp bridges

**Current state:** v2.0.0, ~35K LOC Python, Windows (full) + Linux/macOS (headless services via Docker)

**One-liner install:**
```powershell
powershell -c "irm https://raw.githubusercontent.com/StefSNS/LAIS--Local-AI-system/main/install.ps1 | iex"
```

Or Docker:
```bash
git clone https://github.com/StefSNS/LAIS--Local-AI-system.git && docker compose up -d
```

**GitHub:** https://github.com/StefSNS/LAIS--Local-AI-system

Happy to answer questions about the architecture, memory design, or token optimization pipeline.

---

## r/selfhosted

**Title:** LAIS v2 — self-hosted multi-agent AI system (voice AI, orchestrator, CLI) with Docker

**Body:**

I've been building a self-hosted multi-agent AI system and just published v2.0.0 with Docker support.

**What it does:**
LAIS runs three autonomous agents on your own hardware:

1. **JARVIS** — voice AI assistant. Talk to it, show it your screen, ask it to control your desktop
2. **AI Engine** — desktop GUI with plugin orchestrator (40+ plugins), RAG pipeline
3. **OpenCode** — CLI coding agent with TDD, code review, debugging skills

All three share memory — JARVIS remembers what OpenCode coded, the AI Engine orchestrates multi-step workflows.

**Self-hosting features:**
- Docker compose (3 services: A2A server, vault MCP, REST API)
- All local — no cloud dependency (API key for Gemini voice, everything else runs locally)
- ~35K LOC Python, runs on modest hardware (~2GB RAM for headless services)
- Cross-platform install (Windows one-liner, Linux/macOS bash script, Docker)

**One-liner:**
```powershell
powershell -c "irm https://raw.githubusercontent.com/StefSNS/LAIS--Local-AI-system/main/install.ps1 | iex"
```

**Docker:**
```bash
docker compose up -d
```

**GitHub:** https://github.com/StefSNS/LAIS--Local-AI-system

**License:** CC BY-NC 4.0 (free for non-commercial self-hosting)
