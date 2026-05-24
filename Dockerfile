FROM python:3.11-slim AS base

WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml setup.py ./
COPY __init__.py ./__init__.py
COPY models/__init__.py ./models/__init__.py
COPY models/ai_engine/__init__.py ./models/ai_engine/__init__.py

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir mcp

COPY . .

RUN python -c "import compileall; compileall.compile_dir('.', quiet=1)"

FROM base AS a2a-server
EXPOSE 8020
CMD ["python", "-m", "models.ai_engine.unified_layer.a2a_server"]

FROM base AS vault-server
EXPOSE 8000
ENV LAIS_VAULT_PATH=/app/vault
CMD ["python", "-m", "models.ai_engine.mcp_servers.vault_mcp.src.lais_vault_mcp.server"]

FROM base AS api-server
EXPOSE 8080
CMD ["python", "/app/docker/api_server.py"]

FROM base AS all-in-one
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 8020 8000 8080
CMD ["/entrypoint.sh"]
