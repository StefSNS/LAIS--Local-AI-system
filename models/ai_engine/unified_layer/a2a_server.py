"""
A2A Agent-to-Agent HTTP Server.
Exposes Agent Card discovery and task endpoints per A2A v1.0 spec.
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from .protocol_layer import ProtocolLayer, A2AAgentCard

A2A_VERSION = "1.0"
DEFAULT_PORT = 8020


class A2ARequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for A2A protocol endpoints."""

    protocol_layer: Optional[ProtocolLayer] = None
    server_name: str = "LAIS"
    server_description: str = "Local AI System — multi-agent orchestration"

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def _send_error(self, message: str, status: int = 400):
        self._send_json({"error": message, "status": status}, status)

    def _get_agent_card(self) -> dict:
        """Build the A2A Agent Card for this server."""
        agents = self.protocol_layer.list_a2a_agents() if self.protocol_layer else []
        return {
            "name": self.server_name,
            "description": self.server_description,
            "url": f"http://localhost:{DEFAULT_PORT}",
            "version": A2A_VERSION,
            "capabilities": [
                "a2a/task_submit",
                "a2a/task_status",
                "a2a/agent_discovery",
            ],
            "agents": agents,
            "authentication": None,
        }

    def _parse_path(self) -> tuple:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        return path, parsed

    def do_GET(self):
        path, parsed = self._parse_path()

        if path in ("/.well-known/agent-card", "/a2a/agent-card"):
            card = self._get_agent_card()
            self._send_json(card)

        elif path.startswith("/a2a/tasks/"):
            task_id = path[len("/a2a/tasks/"):]
            if not task_id:
                return self._send_error("Missing task_id", 400)
            task = self.protocol_layer.get_task(task_id) if self.protocol_layer else None
            if not task:
                return self._send_error("Task not found", 404)
            self._send_json(task)

        elif path == "/a2a/tasks":
            agent = parsed.query and dict(p.split("=") for p in parsed.query.split("&") if "=" in p).get("agent")
            status_filter = parsed.query and dict(p.split("=") for p in parsed.query.split("&") if "=" in p).get("status")
            tasks = self.protocol_layer.list_tasks(agent=agent, status=status_filter) if self.protocol_layer else []
            self._send_json({"tasks": tasks})

        elif path == "/status":
            status = self.protocol_layer.get_status() if self.protocol_layer else {}
            self._send_json(status)

        else:
            self._send_error("Not found", 404)

    def do_POST(self):
        path, _ = self._parse_path()
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return self._send_error("Invalid JSON body")

        if path == "/a2a/tasks":
            if not self.protocol_layer:
                return self._send_error("Protocol layer not initialized", 500)
            from_agent = data.get("from_agent", "remote")
            to_agent = data.get("to_agent")
            task_type = data.get("task_type", "generic")
            payload = data.get("payload", {})
            priority = data.get("priority", "normal")

            if not to_agent:
                return self._send_error("to_agent is required")

            task = self.protocol_layer.delegate_task(
                from_agent=from_agent,
                to_agent=to_agent,
                task_type=task_type,
                payload=payload,
                priority=priority,
            )
            self._send_json(task.to_dict(), 201)

        elif path == "/a2a/message":
            if not self.protocol_layer:
                return self._send_error("Protocol layer not initialized", 500)
            from_agent = data.get("from_agent", "remote")
            to_agent = data.get("to_agent")
            message = data.get("message", "")
            msg_type = data.get("message_type", "request")

            if not to_agent or not message:
                return self._send_error("to_agent and message are required")

            msg_id = self.protocol_layer.send_a2a_message(
                from_agent=from_agent,
                to_agent=to_agent,
                message=message,
                message_type=msg_type,
            )
            if msg_id:
                self._send_json({"message_id": msg_id, "status": "sent"}, 201)
            else:
                self._send_error(f"Unknown agent: {to_agent}", 404)

        else:
            self._send_error("Not found", 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass


class A2AServer:
    """
    Lightweight A2A HTTP server.
    Serves Agent Card discovery + task endpoints in a background thread.
    """

    def __init__(
        self,
        protocol_layer: ProtocolLayer,
        host: str = "127.0.0.1",
        port: int = DEFAULT_PORT,
        name: str = "LAIS",
        description: str = "Local AI System — multi-agent orchestration",
    ):
        self.protocol_layer = protocol_layer
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False

        A2ARequestHandler.protocol_layer = protocol_layer
        A2ARequestHandler.server_name = name
        A2ARequestHandler.server_description = description

    def start(self):
        """Start A2A server in background thread."""
        if self.running:
            return

        self.server = HTTPServer((self.host, self.port), A2ARequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.running = True

    def stop(self):
        """Stop the A2A server."""
        if self.server and self.running:
            self.server.shutdown()
            self.server.server_close()
            self.running = False

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


def start_a2a_server(
    protocol_layer: Optional[ProtocolLayer] = None,
    port: int = DEFAULT_PORT,
) -> A2AServer:
    """Factory: create, register, and start A2A server."""
    if protocol_layer is None:
        protocol_layer = ProtocolLayer()

    server = A2AServer(protocol_layer, port=port)
    server.start()
    return server


if __name__ == "__main__":
    proto = ProtocolLayer()

    proto.register_local_agent(
        "lais", "LAIS GUI", "GUI agent with customtkinter interface",
        ["gui", "chat", "search", "vault_write"]
    )
    proto.register_local_agent(
        "jarvis", "Jarvis Voice/Text", "Voice and text-based agent",
        ["voice", "text", "search", "memory_write"]
    )
    proto.register_local_agent(
        "opencode", "OpenCode CLI", "CLI agent with code execution",
        ["code", "shell", "search", "file_write", "api"]
    )

    srv = start_a2a_server(proto)
    print(f"A2A server running at {srv.url}")
    print(f"  Agent Card:  {srv.url}/.well-known/agent-card")
    print(f"  Tasks:       {srv.url}/a2a/tasks")
    print(f"  Status:      {srv.url}/status")
    print("Press Ctrl+C to stop.")

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        srv.stop()
        print("\nA2A server stopped.")
