"""
Agent Dashboard - Single web UI for monitoring all agents
Lightweight HTTP server showing vault stats, agent status, tasks, and activity.
"""

import json
import os
import sys
import threading
import time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from io import BytesIO

UNIFIED_LAYER_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(UNIFIED_LAYER_PATH))

DASHBOARD_PORT = 8888


def get_dashboard_data():
    """Collect all system data for the dashboard."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "vault": {},
        "agents": {},
        "tasks": {},
        "sync": {},
        "recent_activity": []
    }
    
    # Agent statuses (static, fast)
    data["agents"] = {
        "lais": {
            "type": "GUI Assistant",
            "model": "Phi-3 (local)",
            "interface": "Desktop (customtkinter)",
            "status": "active"
        },
        "jarvis": {
            "type": "Voice Assistant",
            "model": "Gemini Flash (cloud)",
            "interface": "Audio (Google Live API)",
            "status": "active"
        },
        "opencode": {
            "type": "Development Agent",
            "model": "Configurable",
            "interface": "Terminal (TUI)",
            "status": "active"
        }
    }
    
    # Vault stats (fast, no embeddings)
    try:
        vault_path = Path(os.environ.get("LAIS_VAULT_PATH", r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain"))
        notes = list(vault_path.rglob("*.md"))
        folders = set(n.parent.name for n in notes)
        data["vault"] = {
            "notes": len(notes),
            "folders": len(folders),
            "last_updated": datetime.fromtimestamp(max(n.stat().st_mtime for n in notes)).isoformat() if notes else "N/A"
        }
    except Exception as e:
        data["vault"] = {"error": str(e)}
    
    # Task queue (fast)
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from unified_layer.task_queue import load_task_queue
        queue = load_task_queue()
        status = queue.get_queue_status()
        status["pending_list"] = queue.get_pending_tasks()
        status["active_list"] = queue.get_active_tasks()
        data["tasks"] = status
    except Exception as e:
        data["tasks"] = {"error": str(e), "pending": 0, "in_progress": 0, "completed": 0, "pending_list": [], "active_list": []}
    
    # Memory sync (fast)
    try:
        from unified_layer.memory_sync import load_shared_memory
        sync = load_shared_memory()
        data["sync"] = sync.get_sync_status()
        data["recent_activity"] = sync.get_recent_updates(since_minutes=60, limit=10)
    except Exception as e:
        data["sync"] = {"error": str(e), "total_entries": 0}
    
    return data


def generate_html(data):
    """Generate dashboard HTML."""
    ts = data['timestamp'][:19].replace('T', ' ')
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified Brain - Agent Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #58a6ff; margin-bottom: 10px; font-size: 24px; }
        h2 { color: #58a6ff; margin: 20px 0 10px; font-size: 18px; border-bottom: 1px solid #21262d; padding-bottom: 5px; }
        .subtitle { color: #8b949e; margin-bottom: 20px; font-size: 14px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .card { background: #161b22; border: 1px solid #21262d; border-radius: 8px; padding: 15px; }
        .card h3 { color: #58a6ff; font-size: 14px; margin-bottom: 10px; }
        .stat { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #21262d; }
        .stat:last-child { border-bottom: none; }
        .stat-label { color: #8b949e; }
        .stat-value { color: #58a6ff; font-weight: 600; }
        .agent { display: flex; align-items: center; gap: 10px; padding: 10px; background: #0d1117; border-radius: 6px; margin-bottom: 8px; }
        .agent-dot { width: 10px; height: 10px; border-radius: 50%; background: #2ea043; }
        .agent-name { font-weight: 600; color: #c9d1d9; }
        .agent-type { color: #8b949e; font-size: 12px; }
        .task { padding: 8px; background: #0d1117; border-radius: 6px; margin-bottom: 6px; border-left: 3px solid #58a6ff; }
        .task.urgent { border-left-color: #f85149; }
        .task.high { border-left-color: #f0883e; }
        .task-title { font-weight: 500; }
        .task-meta { color: #8b949e; font-size: 12px; }
        .activity { padding: 6px 0; border-bottom: 1px solid #21262d; font-size: 13px; }
        .activity:last-child { border-bottom: none; }
        .activity-time { color: #8b949e; }
        .activity-agent { color: #58a6ff; }
        .refresh { position: fixed; top: 20px; right: 20px; background: #238636; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; }
        .refresh:hover { background: #2ea043; }
    </style>
</head>
<body>
    <button class="refresh" onclick="location.reload()">Refresh</button>
    <div class="container">
        <h1>Unified Brain Dashboard</h1>
        <p class="subtitle">Last updated: """ + ts + """</p>
        
        <h2>Agents</h2>
        <div class="grid">
            <div class="card">
"""
    
    for name, info in data.get("agents", {}).items():
        status = info.get("status", "unknown")
        dot_color = "#2ea043" if status == "active" else "#8b949e"
        html += f"""
                <div class="agent">
                    <div class="agent-dot" style="background: {dot_color};"></div>
                    <div>
                        <div class="agent-name">{name.title()}</div>
                        <div class="agent-type">{info.get('type', '')} | {info.get('model', '')}</div>
                        <div class="agent-type">{info.get('interface', '')}</div>
                    </div>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <h2>Vault Statistics</h2>
        <div class="grid">
            <div class="card">
                <h3>Knowledge Base</h3>
"""
    
    vault = data.get("vault", {})
    for key, value in vault.items():
        if key in ("topic_summary", "knowledge_gaps", "error"):
            continue
        html += f"""
                <div class="stat">
                    <span class="stat-label">{key.replace('_', ' ').title()}</span>
                    <span class="stat-value">{value}</span>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <h2>Task Queue</h2>
        <div class="grid">
            <div class="card">
                <h3>Queue Status</h3>
"""
    
    tasks = data.get("tasks", {})
    for key in ["pending", "in_progress", "completed"]:
        if key in tasks:
            html += f"""
                <div class="stat">
                    <span class="stat-label">{key.replace('_', ' ').title()}</span>
                    <span class="stat-value">{tasks[key]}</span>
                </div>
"""
    
    html += """
                <h3 style="margin-top: 15px;">Pending Tasks</h3>
"""
    
    for task in tasks.get("pending_list", [])[:5]:
        priority = task.get("priority", "normal")
        html += f"""
                <div class="task {priority}">
                    <div class="task-title">{task.get('title', 'Untitled')}</div>
                    <div class="task-meta">Assigned to: {task.get('assigned_to', 'unassigned')} | Priority: {priority}</div>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <h2>Memory Sync</h2>
        <div class="grid">
            <div class="card">
                <h3>Shared Memory</h3>
"""
    
    sync = data.get("sync", {})
    for key in ["total_entries", "last_sync"]:
        if key in sync:
            html += f"""
                <div class="stat">
                    <span class="stat-label">{key.replace('_', ' ').title()}</span>
                    <span class="stat-value">{sync[key]}</span>
                </div>
"""
    
    html += """
                <h3 style="margin-top: 15px;">Recent Activity</h3>
"""
    
    for activity in data.get("recent_activity", [])[:10]:
        html += f"""
                <div class="activity">
                    <span class="activity-time">{activity.get('updated', '')[:19]}</span> | 
                    <span class="activity-agent">[{activity.get('agent', '')}]</span> 
                    {activity.get('key', '')[:50]}
                </div>
"""
    
    html += """
            </div>
        </div>
    </div>
</body>
</html>"""
    
    return html


class DashboardHandler(SimpleHTTPRequestHandler):
    """HTTP handler for dashboard."""
    
    def do_GET(self):
        if self.path == "/" or self.path == "/dashboard":
            data = get_dashboard_data()
            html = generate_html(data)
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-length", len(html.encode()))
            self.end_headers()
            self.wfile.write(html.encode())
        elif self.path == "/api/status":
            data = get_dashboard_data()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", len(json.dumps(data).encode()))
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass


def run_dashboard(port=DASHBOARD_PORT):
    """Start the dashboard server."""
    flag_file = Path(__file__).resolve().parent.parent / "knowledge" / "memory" / "sync" / "dashboard_running.flag"
    flag_file.parent.mkdir(parents=True, exist_ok=True)
    flag_file.write_text(datetime.now().isoformat(), encoding="utf-8")
    
    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"Dashboard running at http://127.0.0.1:{port}")
    print(f"API endpoint: http://127.0.0.1:{port}/api/status")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    import webbrowser
    
    port = DASHBOARD_PORT
    print(f"Starting Unified Brain Dashboard on port {port}...")
    
    threading = __import__("threading")
    t = threading.Thread(target=run_dashboard, args=(port,), daemon=True)
    t.start()
    
    try:
        webbrowser.open(f"http://127.0.0.1:{port}")
        print("Dashboard opened in browser.")
    except Exception as e:
        pass
    
    print(f"Dashboard running at http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            __import__("time").sleep(1)
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
