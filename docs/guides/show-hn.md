# HackerNews Post

**Title:** LAIS — triple-agent AI OS with voice, GUI, and CLI agents sharing one brain

**URL:** https://github.com/StefSNS/LAIS--Local-AI-system

---

I built a local AI system that runs three autonomous agents simultaneously:

**JARVIS** — Voice AI with Gemini Live, screen vision, webcam, desktop control, and a 9-agent security grid.

**AI Engine** — Desktop GUI orchestrator with 40+ hot-loaded plugins, RAG pipeline, and multi-agent routing.

**OpenCode** — CLI agent with 30+ coding skills (TDD, code review, refactoring, debugging).

All three share a unified 4-layer memory (Hot/Warm/Cold/Crystallized) and communicate through an 18-module protocol (A2A, WebSocket, MCP bridge, shared memory, trust scoring, consensus).

**Why this exists:**
Existing agent frameworks are single-modality. OpenClaw is messaging-first. Hermes Agent is CLI-only. AutoGPT is task-focused. None run voice + GUI + CLI simultaneously with shared memory.

**Key architectural decisions:**
- 4-layer memory with graduated compression (100% / 60% / 20% / 90%)
- 4-engine token optimization pipeline that compresses prompts 40-60%
- Progressive skill loading (metadata → body → resources)
- Cross-agent memories — JARVIS remembers what OpenCode did

**Stack:** Python 3.11+ | Google Gemini | customtkinter (GUI) | FastMCP (vault) | ~35K LOC

**One-liner install:**
```powershell
powershell -c "irm https://raw.githubusercontent.com/StefSNS/LAIS--Local-AI-system/main/install.ps1 | iex"
```

Docker support and Linux/macOS install scripts also available.

https://github.com/StefSNS/LAIS--Local-AI-system
