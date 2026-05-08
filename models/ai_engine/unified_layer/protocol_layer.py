"""
Protocol Layer - Phase 5 of Architecture Evolution
MCP (Model Context Protocol) client + A2A (Agent-to-Agent) protocol support.
Inspired by Hermes Agent's MCP/A2A integration plans.
"""

import json
import re
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from threading import Lock

MCP_CONFIG_FILE = Path(
    r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\mcp_config.json"
)
A2A_CONFIG_FILE = Path(
    r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\a2a_config.json"
)
AGENT_REGISTRY_FILE = Path(
    r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\agent_registry.json"
)
PROTOCOL_LOG_FILE = Path(
    r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\protocol_log.json"
)

for f in [MCP_CONFIG_FILE, A2A_CONFIG_FILE, AGENT_REGISTRY_FILE, PROTOCOL_LOG_FILE]:
    f.parent.mkdir(parents=True, exist_ok=True)

LOCK = Lock()


class MCPCapability:
    """Represents an MCP tool capability."""

    def __init__(self, name: str, description: str, input_schema: Dict):
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class MCPServer:
    """Represents an MCP server connection."""

    def __init__(self, server_id: str, name: str, transport: str, config: Dict):
        self.server_id = server_id
        self.name = name
        self.transport = transport
        self.config = config
        self.connected = False
        self.capabilities: List[MCPCapability] = []
        self.last_seen = None

    def to_dict(self) -> Dict:
        return {
            "server_id": self.server_id,
            "name": self.name,
            "transport": self.transport,
            "config": self.config,
            "connected": self.connected,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "last_seen": self.last_seen,
        }


class A2AAgentCard:
    """Represents an A2A agent capability card."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: List[str],
        url: str = "",
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.url = url
        self.online = True
        self.last_seen = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "url": self.url,
            "online": self.online,
            "last_seen": self.last_seen,
        }


class A2ATask:
    """Represents an A2A task delegation."""

    def __init__(
        self,
        task_id: str,
        from_agent: str,
        to_agent: str,
        task_type: str,
        payload: Dict,
        priority: str = "normal",
    ):
        self.task_id = task_id
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.task_type = task_type
        self.payload = payload
        self.priority = priority
        self.status = "pending"
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
        self.result = None
        self.error = None

    def complete(self, result: Any):
        self.status = "completed"
        self.result = result
        self.completed_at = datetime.now().isoformat()

    def fail(self, error: str):
        self.status = "failed"
        self.error = error
        self.completed_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
        }


class ProtocolLayer:
    """
    Protocol support for external tool and agent communication.
    - MCP client: discover and call MCP server tools
    - A2A protocol: inter-agent task delegation and discovery
    - Local agent registry: discover agents within our own system
    """

    def __init__(self):
        self.mcp_servers: Dict[str, MCPServer] = {}
        self.a2a_agents: Dict[str, A2AAgentCard] = {}
        self.a2a_tasks: Dict[str, A2ATask] = {}
        self.local_agent_handlers: Dict[str, callable] = {}

        self._load_mcp_config()
        self._load_a2a_config()
        self._load_agent_registry()

    def _load_mcp_config(self):
        """Load MCP server configuration."""
        if MCP_CONFIG_FILE.exists():
            try:
                data = json.loads(MCP_CONFIG_FILE.read_text(encoding="utf-8"))
                for srv_data in data:
                    srv = MCPServer(
                        server_id=srv_data["server_id"],
                        name=srv_data["name"],
                        transport=srv_data.get("transport", "stdio"),
                        config=srv_data.get("config", {}),
                    )
                    srv.connected = srv_data.get("connected", False)
                    self.mcp_servers[srv.server_id] = srv
            except Exception:
                pass

    def _load_a2a_config(self):
        """Load A2A agent configuration."""
        if A2A_CONFIG_FILE.exists():
            try:
                data = json.loads(A2A_CONFIG_FILE.read_text(encoding="utf-8"))
                for agent_data in data:
                    agent = A2AAgentCard(
                        agent_id=agent_data["agent_id"],
                        name=agent_data["name"],
                        description=agent_data.get("description", ""),
                        capabilities=agent_data.get("capabilities", []),
                        url=agent_data.get("url", ""),
                    )
                    self.a2a_agents[agent.agent_id] = agent
            except Exception:
                pass

    def _load_agent_registry(self):
        """Load local agent handler registry."""
        if AGENT_REGISTRY_FILE.exists():
            try:
                data = json.loads(AGENT_REGISTRY_FILE.read_text(encoding="utf-8"))
                for handler_data in data:
                    agent_id = handler_data["agent_id"]
                    if agent_id not in self.local_agent_handlers:
                        self.local_agent_handlers[agent_id] = handler_data

            except Exception:
                pass

    def _save_mcp_config(self):
        """Save MCP configuration."""
        with LOCK:
            data = [srv.to_dict() for srv in self.mcp_servers.values()]
            MCP_CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _save_a2a_config(self):
        """Save A2A configuration."""
        with LOCK:
            data = [agent.to_dict() for agent in self.a2a_agents.values()]
            A2A_CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _save_agent_registry(self):
        """Save local agent registry."""
        with LOCK:
            data = list(self.local_agent_handlers.values())
            AGENT_REGISTRY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _log_protocol_event(self, event: str, detail: str):
        """Log a protocol event."""
        log_entry = {
            "event": event,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            if PROTOCOL_LOG_FILE.exists():
                log = json.loads(PROTOCOL_LOG_FILE.read_text(encoding="utf-8"))
            else:
                log = []
            log.append(log_entry)
            PROTOCOL_LOG_FILE.write_text(
                json.dumps(log[-200:], indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    # ---- MCP ----

    def register_mcp_server(
        self, name: str, transport: str = "stdio", config: Optional[Dict] = None
    ) -> MCPServer:
        """Register an MCP server."""
        server_id = f"mcp_{name.lower().replace(' ', '_')}"
        server = MCPServer(
            server_id=server_id,
            name=name,
            transport=transport,
            config=config or {},
        )
        self.mcp_servers[server_id] = server
        self._save_mcp_config()
        self._log_protocol_event("mcp_server_registered", name)
        return server

    def list_mcp_servers(self) -> List[Dict]:
        """List all registered MCP servers."""
        return [srv.to_dict() for srv in self.mcp_servers.values()]

    def get_mcp_tools(self, server_id: str) -> List[Dict]:
        """Get tools from an MCP server."""
        srv = self.mcp_servers.get(server_id)
        if not srv:
            return []
        return [c.to_dict() for c in srv.capabilities]

    def call_mcp_tool(
        self, server_id: str, tool_name: str, args: Optional[Dict] = None
    ) -> Tuple[bool, Any]:
        """
        Call an MCP tool.
        Returns (success, result).
        """
        srv = self.mcp_servers.get(server_id)
        if not srv:
            return False, f"MCP server not found: {server_id}"

        if not srv.connected:
            return False, f"MCP server not connected: {srv.name}"

        tool = next(
            (c for c in srv.capabilities if c.name == tool_name), None
        )
        if not tool:
            return False, f"Tool not found: {tool_name}"

        # In a real implementation, this would make an HTTP/stdio call to the MCP server
        # For now, this is a placeholder that records the intent
        self._log_protocol_event(
            "mcp_tool_called", f"{server_id}/{tool_name}"
        )
        return True, {"status": "call_recorded", "tool": tool_name}

    # ---- A2A ----

    def register_a2a_agent(
        self,
        name: str,
        description: str,
        capabilities: List[str],
        url: str = "",
    ) -> A2AAgentCard:
        """Register an A2A-capable agent."""
        agent_id = f"a2a_{name.lower().replace(' ', '_')}"
        agent = A2AAgentCard(
            agent_id=agent_id,
            name=name,
            description=description,
            capabilities=capabilities,
        )
        if url:
            agent.url = url
        self.a2a_agents[agent_id] = agent
        self._save_a2a_config()
        self._log_protocol_event("a2a_agent_registered", name)
        return agent

    def discover_agents(
        self, required_capability: Optional[str] = None
    ) -> List[Dict]:
        """Discover agents by capability."""
        results = []
        for agent in self.a2a_agents.values():
            if not agent.online:
                continue
            if required_capability and required_capability not in agent.capabilities:
                continue
            results.append(agent.to_dict())
        return results

    def delegate_task(
        self,
        from_agent: str,
        to_agent: str,
        task_type: str,
        payload: Dict,
        priority: str = "normal",
    ) -> A2ATask:
        """Delegate a task to another agent via A2A."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = A2ATask(
            task_id=task_id,
            from_agent=from_agent,
            to_agent=to_agent,
            task_type=task_type,
            payload=payload,
            priority=priority,
        )
        self.a2a_tasks[task_id] = task

        # If the target agent is local, try to execute via handler
        if to_agent in self.local_agent_handlers:
            self._execute_local_task(task)
        else:
            self._log_protocol_event(
                "a2a_task_delegated", f"{from_agent} -> {to_agent}: {task_type}"
            )

        return task

    def _execute_local_task(self, task: A2ATask):
        """Execute a task on a local agent."""
        try:
            handler_info = self.local_agent_handlers[task.to_agent]
            # In a real implementation, this would call the agent's handler
            task.complete({"status": "executed_locally", "handler": handler_info.get("name", task.to_agent)})
        except Exception as e:
            task.fail(str(e))

        self._log_protocol_event(
            "a2a_task_executed", f"{task.from_agent} -> {task.to_agent}: {task.status}"
        )

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get an A2A task by ID."""
        task = self.a2a_tasks.get(task_id)
        return task.to_dict() if task else None

    def list_tasks(self, agent: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """List A2A tasks."""
        tasks = []
        for t in self.a2a_tasks.values():
            if agent and t.from_agent != agent and t.to_agent != agent:
                continue
            if status and t.status != status:
                continue
            tasks.append(t.to_dict())
        return tasks

    # ---- Local Agent Registry ----

    def register_local_agent(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: List[str],
        handler: Optional[callable] = None,
    ):
        """Register a local agent for A2A communication."""
        agent_data = {
            "agent_id": agent_id,
            "name": name,
            "description": description,
            "capabilities": capabilities,
            "registered_at": datetime.now().isoformat(),
        }

        if handler:
            agent_data["handler"] = handler

        self.local_agent_handlers[agent_id] = agent_data
        self._save_agent_registry()

        # Also register as A2A agent
        self.register_a2a_agent(
            name=name,
            description=description,
            capabilities=capabilities,
        )

    def send_a2a_message(
        self,
        from_agent: str,
        to_agent: str,
        message: str,
        message_type: str = "request",
    ) -> Optional[str]:
        """
        Send a message between agents using A2A protocol.
        Returns message ID if sent successfully, None otherwise.
        """
        if to_agent not in self.a2a_agents and to_agent not in self.local_agent_handlers:
            self._log_protocol_event("a2a_send_failed", f"Unknown agent: {to_agent}")
            return None

        if message_type == "task":
            task = self.delegate_task(
                from_agent=from_agent,
                to_agent=to_agent,
                task_type="message_task",
                payload={"message": message},
            )
            return task.task_id if task else None
        else:
            # Log the communication
            self._log_protocol_event(
                "a2a_message",
                f"{from_agent} -> {to_agent}: {message[:50]}"
            )
            # Return a dummy ID for tracking
            return f"msg_{from_agent}_{to_agent}_{len(self.a2a_tasks)}"

    def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """Get capabilities of a local agent."""
        agent = self.local_agent_handlers.get(agent_id)
        if agent:
            return agent.get("capabilities", [])
        a2a = self.a2a_agents.get(f"a2a_{agent_id}")
        if a2a:
            return a2a.capabilities
        return []

    def get_status(self) -> Dict[str, Any]:
        """Get protocol layer status."""
        return {
            "mcp_servers": len(self.mcp_servers),
            "mcp_connected": sum(1 for s in self.mcp_servers.values() if s.connected),
            "a2a_agents": len(self.a2a_agents),
            "a2a_online": sum(1 for a in self.a2a_agents.values() if a.online),
            "a2a_tasks": len(self.a2a_tasks),
            "local_agents": len(self.local_agent_handlers),
        }


def load_protocol_layer() -> ProtocolLayer:
    """Factory function."""
    return ProtocolLayer()


if __name__ == "__main__":
    import sys
    sys.path.insert(
        0, r"str(Path(__file__).resolve().parent.parent)"
    )

    print("=== Protocol Layer - Phase 5 ===\n")

    proto = load_protocol_layer()

    # Register local agents
    print("--- Registering Local Agents ---")
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

    # Register external A2A agent (placeholder)
    print("\n--- Registering External A2A Agent ---")
    proto.register_a2a_agent(
        name="Hermes Research Agent",
        description="Web research and information gathering",
        capabilities=["research", "web_search", "summarization"],
        url="http://localhost:8080/hermes"
    )

    # Discover agents
    print("\n--- Discover Agents ---")
    agents = proto.discover_agents()
    for a in agents:
        print(f"  {a['name']}: {a['capabilities']}")

    # Delegate tasks
    print("\n--- Delegating Tasks ---")
    t1 = proto.delegate_task(
        "lais", "opencode", "code_review",
        {"file": "unified_layer/memory_sqlite.py", "focus": "performance"},
        priority="high"
    )
    print(f"  Task {t1.task_id}: {t1.from_agent} -> {t1.to_agent} ({t1.status})")

    t2 = proto.delegate_task(
        "opencode", "lais", "display_results",
        {"results": "Found 3 matches"},
        priority="normal"
    )
    print(f"  Task {t2.task_id}: {t2.from_agent} -> {t2.to_agent} ({t2.status})")

    # MCP server registration (placeholder)
    print("\n--- MCP Server Registration ---")
    proto.register_mcp_server(
        "filesystem", "stdio",
        {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/vault"]}
    )
    proto.register_mcp_server(
        "web_search", "http",
        {"url": "http://localhost:3001"}
    )

    servers = proto.list_mcp_servers()
    for s in servers:
        print(f"  {s['name']} ({s['transport']}): {s['connected']}")

    print("\n--- Status ---")
    status = proto.get_status()
    print(json.dumps(status, indent=2))

    print("\nPhase 5 protocol layer test complete.")
