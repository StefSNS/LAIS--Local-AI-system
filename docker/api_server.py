"""LAIS REST API Server — headless entry point for Docker deployments."""
import json
import os
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

PORT = int(os.environ.get("LAIS_API_PORT", 8080))

from models.ai_engine.unified_layer.token_optimizer import get_token_optimizer
from models.ai_engine.unified_layer.a2a_server import A2AServer, ProtocolLayer

protocol = ProtocolLayer()

class APIHandler(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")
        if path == "/health":
            self._json({"status": "ok", "version": "2.0.0", "service": "LAIS API"})
        elif path == "/agents":
            self._json({"agents": protocol.list_a2a_agents()})
        elif path == "/token-report":
            opt = get_token_optimizer("docker")
            self._json(opt.get_report() if hasattr(opt, "get_report") else {"message": "Token optimizer available"})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        if path == "/a2a/task":
            result = protocol.send_task(body.get("agent", ""), body.get("task", ""))
            self._json({"result": result})
        else:
            self._json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        print(f"[API] {args[0]} {args[1]} {args[2]}")

def main():
    server = HTTPServer(("0.0.0.0", PORT), APIHandler)
    print(f"LAIS API server running on http://0.0.0.0:{PORT}")
    print(f"  GET  /health       — health check")
    print(f"  GET  /agents       — list registered agents")
    print(f"  GET  /token-report — token optimization report")
    print(f"  POST /a2a/task     — send task to agent")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    main()
