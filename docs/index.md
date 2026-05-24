# LAIS — Local AI System

> **Three autonomous agents. One shared brain. Zero cloud dependency.**

LAIS is a multi-agent AI operating system that runs three autonomous agents simultaneously on your local machine:

| Agent | Interface | Purpose |
|-------|-----------|---------|
| **JARVIS** (Mark XXXIX) | Voice + Vision | Real-time voice AI via Gemini Live, screen/webcam analysis, desktop control, 9-agent security grid |
| **AI Engine** | Desktop GUI | Plugin orchestrator with 40+ hot-loaded plugins, RAG pipeline, multi-agent routing |
| **OpenCode** | CLI Terminal | 30+ coding skills: TDD, refactoring, code review, research, debugging |

## Quick Links

- [Getting Started](getting-started.md) — Install and run LAIS in 5 minutes
- [Architecture Overview](architecture.md) — System design, agent loop, memory layers
- [JARVIS Voice AI](agents/jarvis.md) — Voice commands, screen vision, desktop control
- [AI Engine](agents/ai-engine.md) — Plugin system, orchestrator, multi-agent routing
- [Memory Architecture](memory.md) — 4-layer hot/warm/cold/crystallized memory
- [CoComm Protocol](cocomm.md) — Cross-agent communication with 18 modules
- [Token Optimization](token-optimizer.md) — Multi-library compression pipeline
- [Docker Deployment](docker.md) — Containerized headless services

## Key Features

- **Triple-Agent Architecture** — Voice AI + GUI + CLI with shared memory
- **4-Layer Memory (v3.0)** — Hot (100%), Warm (60%), Cold (20%), Crystallized (90%)
- **Token Optimization Pipeline (v1.0.0)** — Claw, LLMLingua, TokenPruner, Shekel, ResponseCache
- **CoComm Protocol (18 modules)** — A2A server, WebSocket, MCP bridge, shared memory, trust, consensus
- **40+ Hot-Loaded Plugins** — Dynamic plugin system with file watcher
- **30+ Skills** — TDD, code review, refactoring, debugging, research
- **9-Agent Security Grid** — Network shield, code sentry, file watchdog, anomaly detection
- **Cross-Platform** — Windows (full), Linux/macOS (headless services)

## Comparison

| Feature | LAIS | OpenClaw | Hermes Agent | AutoGPT |
|---------|------|----------|--------------|---------|
| Voice AI | ✅ JARVIS | ❌ | ❌ | ❌ |
| GUI Orchestrator | ✅ AI Engine | ❌ | ❌ | ❌ |
| CLI Coder | ✅ OpenCode | ❌ | ✅ | ❌ |
| 4-Layer Memory | ✅ v3.0 | ❌ | ❌ | ❌ |
| Token Optimization | ✅ 4-engine | ❌ | ❌ | ❌ |
| Cross-Agent Protocol | ✅ 18 modules | ❌ | ❌ | ❌ |
| 9-Agent Security | ✅ | ❌ | ❌ | ❌ |
| Messaging Gateway | ✅ TG/DC/WA | ✅ TG | ❌ | ❌ |
| Docker Support | ✅ | ✅ | ❌ | ✅ |
| Platform | Windows/Linux | Cross | Cross | Cross |

## Install

**Windows (one-liner):**
```powershell
powershell -c "irm https://raw.githubusercontent.com/StefSNS/LAIS--Local-AI-system/main/install.ps1 | iex"
```

**Linux/macOS:**
```bash
bash <(curl -s https://raw.githubusercontent.com/StefSNS/LAIS--Local-AI-system/main/install.sh)
```

**Docker:**
```bash
docker compose up -d
```

## License

CC BY-NC 4.0 — Free for non-commercial use.
