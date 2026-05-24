#!/bin/bash
# LAIS Docker entrypoint — starts configured services
set -e

SERVICES=${LAIS_SERVICES:-"api,vault,a2a"}

if [[ "$SERVICES" == *"a2a"* ]]; then
    echo "[ENTRYPOINT] Starting A2A server on :8020"
    python -m models.ai_engine.unified_layer.a2a_server &
fi

if [[ "$SERVICES" == *"vault"* ]]; then
    echo "[ENTRYPOINT] Starting Vault MCP server on :8000"
    python -m mcp_servers.vault_mcp.src.lais_vault_mcp.server &
fi

if [[ "$SERVICES" == *"api"* ]]; then
    echo "[ENTRYPOINT] Starting REST API on :8080"
    python /app/docker/api_server.py &
fi

echo "[ENTRYPOINT] All services started. LAIS v2.0.0 running."
wait
