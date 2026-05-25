# Architecture Overview

## Triple-Agent Architecture

```mermaid
graph TB
    subgraph "JARVIS Mark XXXIX"
        V[Voice I/O<br/>Gemini Live API]
        S[Screen Vision<br/>Webcam Capture]
        D[Desktop Control<br/>Mouse + Keyboard]
        SG[9-Agent Security Grid]
    end

    subgraph "AI Engine"
        PO[Plugin Orchestrator<br/>40+ Hot-Loaded Plugins]
        LLM[Local LLM<br/>RAG Pipeline]
        MR[Multi-Agent Router]
        TM[Token Manager<br/>Pipeline v1.0.0]
    end

    subgraph "OpenCode"
        CS[30+ Coding Skills]
        TD[TDD Workflow]
        CR[Code Review]
        DB[Debugging]
    end

    subgraph "CoComm Protocol"
        A2A[A2A Server<br/>Port 8020]
        WS[WebSocket<br/>Real-Time]
        MCP[MCP Bridge]
        SM[Shared Memory]
        TR[Trust + Consensus]
    end

    subgraph "Unified Memory v3.0"
        HOT[HOT 100%<br/>Active Context]
        WARM[WARM 60%<br/>Summarized]
        COLD[COLD 20%<br/>Compressed]
        CRYST[CRYSTALLIZED 90%<br/>Permanent]
    end

    V --> SG
    S --> SG
    D --> SG
    SG --> A2A
    PO --> MR
    LLM --> MR
    MR --> A2A
    CS --> A2A
    TD --> A2A
    CR --> A2A
    DB --> A2A
    TM --> A2A

    A2A --> SM
    WS --> SM
    MCP --> SM
    SM --> TR

    SM --> HOT
    HOT --> WARM
    WARM --> COLD
    COLD --> CRYST
```

## Agent Loop

```mermaid
sequenceDiagram
    participant U as User
    participant A as Agent
    participant M as Memory
    participant C as CoComm
    participant P as Plugins/Skills

    U->>A: Input (voice/text/action)
    A->>M: Load hot memory
    M-->>A: Context
    A->>C: Query other agents
    C-->>A: Cross-agent context
    A->>P: Load relevant plugins/skills
    P-->>A: Capabilities
    A->>M: Store interaction
    A->>A: Token optimization
    A->>U: Response
```

## Data Flow

```mermaid
flowchart LR
    INPUT[User Input] --> TOKENIZE[Token Optimizer]
    TOKENIZE --> SELECT{Agent Selector}
    SELECT -->|Voice| J[JARVIS]
    SELECT -->|GUI| E[AI Engine]
    SELECT -->|Code| O[OpenCode]
    J --> MEM[Memory Layer]
    E --> MEM
    O --> MEM
    MEM --> COCOMM[CoComm Sync]
    COCOMM --> ALL[All Agents Updated]
```

## Directory Layout

```
LAIS/
├── models/
│   ├── Mark-XXXIX/          # JARVIS voice AI
│   │   ├── main.py          # Voice + vision loop
│   │   └── config/          # API keys
│   └── ai_engine/           # AI Engine
│       ├── unified_layer/   # 60 modules
│       ├── agent/           # Agent modules
│       ├── plugins/         # 40+ plugins
│       ├── skills/          # 30+ skills
│       ├── cli/             # CLI tools
│       └── knowledge/       # RAG, memory
├── config/
│   └── system.json          # Shared config
├── addons/
│   └── token-optimizer/     # v1.0.0 pipeline
│   └── api_server.py        # Headless REST API
├── install.ps1              # Windows one-liner
├── install.sh               # Linux/macOS installer
└── install.py               # 7-phase Python installer
```

## Key Design Decisions

1. **Vault as source of truth** — All protocols, memory, and agent configurations live in an Obsidian vault directory
2. **Memory Architecture v3.0** — Four-tier memory with graduated compression and automatic promotion/demotion
3. **Token Optimization v1.0.0** — Multi-library pipeline that compresses prompts 40-60%
4. **CoComm Protocol** — 18 modules for full cross-agent communication
5. **Progressive Skill Loading** — Skills loaded on demand, not at startup (3 levels: metadata → body → resources)
