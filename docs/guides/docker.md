# Docker Deployment

## Services

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `lais-a2a` | `Dockerfile:a2a-server` | 8020 | A2A agent communication server |
| `lais-vault` | `Dockerfile:vault-server` | 8000 | Obsidian vault MCP server |
| `lais-api` | `Dockerfile:api-server` | 8080 | REST API for headless operation |

## Quick Start

```bash
# Clone and deploy
git clone https://github.com/StefSNS/LAIS--Local-AI-system.git
cd LAIS--Local-AI-system
docker compose up -d

# Check status
curl http://localhost:8080/health
curl http://localhost:8020/status
```

## Single Service

```bash
# Run only the A2A server
docker compose up lais-a2a

# Run only the API server
docker compose up lais-api
```

## All-in-One Container

```bash
docker build --target all-in-one -t lais:latest .
docker run -p 8020:8020 -p 8000:8000 -p 8080:8080 lais:latest
```

Configure which services start via `LAIS_SERVICES` env var:

```bash
docker run -e LAIS_SERVICES="api,vault" lais:latest
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/agents` | List registered agents |
| GET | `/token-report` | Token optimization report |
| POST | `/a2a/task` | Send task to agent |

## Build Your Own Image

```bash
docker build -t lais:latest .
```

Multi-stage build keeps images small — each service image contains only what it needs.
