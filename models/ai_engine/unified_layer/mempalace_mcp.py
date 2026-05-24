"""
MemPalace MCP Server for LAIS.
Exposes 30 MemPalace tools via stdio transport for OpenCode integration.
"""

import subprocess
import sys
import json
from pathlib import Path

MEMPALACE_MCP_PATH = Path(__file__).resolve().parent.parent.parent / ".mempalace" / "mcp"


def start_mcp_server():
    """Start MemPalace MCP server and relay stdio communication."""
    try:
        # Try to use mempalace's built-in mcp command
        result = subprocess.run(
            ["mempalace", "mcp"],
            capture_output=False,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        sys.exit(result.returncode)
    except FileNotFoundError:
        # Fallback: start Python-based MCP server
        print("Error: mempalace mcp not found. Run: pip install mempalace", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    start_mcp_server()