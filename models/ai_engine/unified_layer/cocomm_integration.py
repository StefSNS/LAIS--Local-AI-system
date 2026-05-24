"""
CoComm Integration - LAIS-agent-CoComm Bridge
Integrates all 16 CoComm modules into LAIS unified_layer.
"""

import sys
import importlib.util
from pathlib import Path
from threading import Lock
from typing import Dict, Any, Optional, List


def _import_module_from_file(module_name: str, file_path: Path):
    """Import a module directly from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Add CoComm to path - compute absolute path to integrations folder
_COCOMM_BASE = Path(__file__).resolve().parent.parent.parent.parent.parent / "integrations" / "cocomm" / "src" / "agent_sync"

# Import CoComm modules by name
_session_log = _import_module_from_file("session_log", _COCOMM_BASE / "session_log.py")
_memory_sync = _import_module_from_file("memory_sync", _COCOMM_BASE / "memory_sync.py")
_config = _import_module_from_file("config", _COCOMM_BASE / "config.py")
_roles = _import_module_from_file("roles", _COCOMM_BASE / "roles.py")
_handoff = _import_module_from_file("handoff", _COCOMM_BASE / "handoff.py")
_async_agent = _import_module_from_file("async_agent", _COCOMM_BASE / "async_agent.py")
_goal_planner = _import_module_from_file("goal_planner", _COCOMM_BASE / "goal_planner.py")
_consensus = _import_module_from_file("consensus", _COCOMM_BASE / "consensus.py")
_graph_evolution = _import_module_from_file("graph_evolution", _COCOMM_BASE / "graph_evolution.py")
_trust = _import_module_from_file("trust", _COCOMM_BASE / "trust.py")
_vault_sync = _import_module_from_file("vault_sync", _COCOMM_BASE / "vault_sync.py")
_websocket_server = _import_module_from_file("websocket_server", _COCOMM_BASE / "websocket_server.py")
_a2a_server = _import_module_from_file("a2a_server", _COCOMM_BASE / "a2a_server.py")

# Expose classes
ActiveSessionLog = _session_log.ActiveSessionLog
TriggerManager = _session_log.TriggerManager
FileWatcher = _session_log.FileWatcher
SharedMemory = _memory_sync.SharedMemory
load_shared_memory = _memory_sync.load_shared_memory
AgentConfigLoader = _config.AgentConfigLoader
AgentConfig = _config.AgentConfig
PolicyConfig = _config.PolicyConfig
AgentRole = _roles.AgentRole
RoleRegistry = _roles.RoleRegistry
get_role_registry = _roles.get_role_registry
HandoffAgent = _handoff.HandoffAgent
HandoffChain = _handoff.HandoffChain
HandoffRules = _handoff.HandoffRules
AsyncAgent = _async_agent.AsyncAgent
AsyncAgentPool = _async_agent.AsyncAgentPool
AgentState = _async_agent.AgentState
TaskDAG = _goal_planner.TaskDAG
GoalDecomposer = _goal_planner.GoalDecomposer
create_goal_dag = _goal_planner.create_goal_dag
ConsensusEngine = _consensus.ConsensusEngine
ConsensusRoom = _consensus.ConsensusRoom
VoteStrategy = _consensus.VoteStrategy
EvolvingGraph = _graph_evolution.EvolvingGraph
GraphEvolutionEngine = _graph_evolution.GraphEvolutionEngine
NodeStatus = _graph_evolution.NodeStatus
TrustManager = _trust.TrustManager
AgentReputation = _trust.AgentReputation
VaultIntegration = _vault_sync.VaultIntegration
load_vault_context = _vault_sync.load_vault_context
WebSocketServer = _websocket_server.WebSocketServer
CoCommA2AServer = _a2a_server.A2AServer


class CoCommIntegration:
    """
    Main integration class bridging CoComm modules with LAIS.
    Provides unified access to all 16 CoComm modules while preserving
    LAIS's existing protocol_layer functionality.
    """

    def __init__(self, data_dir: Path = None):
        self._lock = Lock()
        self._initialized = False

        # Data directory
        if data_dir is None:
            base = Path(__file__).resolve().parent.parent / "knowledge" / "memory"
            base.mkdir(parents=True, exist_ok=True)
            data_dir = base / "cocomm"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize all CoComm modules
        self._init_modules()

    def _init_modules(self):
        """Initialize all CoComm modules."""
        # Core modules
        self.session_log = ActiveSessionLog(
            json_path=str(self.data_dir / "active_sessions.json"),
            db_path=str(self.data_dir / "sessions.db"),
            shared_path=str(self.data_dir / "shared_sessions.json")
        )
        self.shared_memory = SharedMemory(self.data_dir)
        self.trigger_manager = self.session_log.trigger_manager

        # Config & Roles
        self.config_loader = AgentConfigLoader(self.data_dir / "agent_configs.json")
        self.role_registry = get_role_registry()

        # Coordination
        self.handoff_rules = HandoffRules()
        self.async_pool = AsyncAgentPool(max_concurrent=5)
        self.goal_decomposer = GoalDecomposer()

        # Advanced coordination
        self.consensus_engine = ConsensusEngine()
        self.graph_engine = GraphEvolutionEngine()
        self.trust_manager = TrustManager()

        # External integrations
        self.vault_integration = VaultIntegration()

        # Server (lazy init)
        self._a2a_server = None
        self._ws_server = None

        self._initialized = True

    @property
    def a2a_server(self):
        """Lazy-load A2A server."""
        if self._a2a_server is None:
            from protocol_layer import ProtocolLayer
            protocol = ProtocolLayer()
            self._a2a_server = CoCommA2AServer(protocol, port=8021)
        return self._a2a_server

    @property
    def ws_server(self):
        """Lazy-load WebSocket server."""
        if self._ws_server is None:
            self._ws_server = WebSocketServer(host="127.0.0.1", port=8022)
        return self._ws_server

    # ---- Session & Task Management ----

    def create_session(self, task_description: str, created_by: str,
                       capabilities_needed: List[str] = None) -> Dict:
        """Create a new cross-agent session."""
        return self.session_log.create_session(task_description, created_by, capabilities_needed)

    def get_session(self) -> Dict:
        """Get current active session."""
        return self.session_log.get_session()

    def update_task(self, task_id: str, status: str, result: str = None):
        """Update task status in session."""
        self.session_log.update_task_status(task_id, status, result)

    # ---- Shared Memory ----

    def store_memory(self, agent: str, key: str, value: str,
                     category: str = "general", priority: str = None) -> bool:
        """Store cross-agent memory."""
        return self.shared_memory.store(agent, key, value, category, priority)

    def retrieve_memory(self, agent: str, key: str = None,
                        category: str = None, limit: int = 10) -> List[Dict]:
        """Retrieve shared memory."""
        return self.shared_memory.retrieve(agent, key, category, limit)

    def search_memory(self, query: str, limit: int = 20) -> List[Dict]:
        """Search across all agent memories."""
        return self.shared_memory.cross_agent_search(query, limit)

    def get_memory_status(self) -> Dict:
        """Get shared memory status."""
        return self.shared_memory.get_sync_status()

    # ---- Roles & Handoff ----

    def assign_role(self, agent_id: str, role: str, metadata: Dict = None) -> bool:
        """Assign role to agent."""
        try:
            agent_role = AgentRole(role.lower())
            self.role_registry.register(agent_role, [agent_id])
            return True
        except (ValueError, AttributeError):
            return False

    def get_agent_role(self, agent_id: str) -> Optional[str]:
        """Get agent's current role."""
        for role, agents in self.role_registry.roles.items():
            if agent_id in agents:
                return role.value
        return None

    def handoff_to(self, from_agent: str, to_agent: str,
                    context: Dict, reason: str = "") -> bool:
        """Execute handoff between agents."""
        return self.handoff_rules.execute_handoff(from_agent, to_agent, context, reason)

    # ---- Async Agent Pool ----

    def spawn_async_agent(self, agent_id: str, task: str,
                          capabilities: List[str]) -> str:
        """Spawn async agent for background task."""
        agent = AsyncAgent(agent_id, capabilities)
        return self.async_pool.submit(agent, task)

    def get_async_status(self, task_id: str) -> Optional[Dict]:
        """Get async task status."""
        return self.async_pool.get_task_status(task_id)

    # ---- Goal Planning ----

    def decompose_goal(self, goal: str, constraints: Dict = None) -> TaskDAG:
        """Decompose high-level goal into task DAG."""
        return self.goal_decomposer.decompose(goal, constraints or {})

    # ---- Consensus ----

    def create_consensus_room(self, room_id: str, agents: List[str],
                              strategy: VoteStrategy = VoteStrategy.MAJORITY) -> ConsensusRoom:
        """Create consensus room for multi-agent decisions."""
        return self.consensus_engine.create_room(room_id, agents, strategy)

    def resolve_via_consensus(self, room_id: str, proposal: Dict) -> Dict:
        """Resolve decision via consensus."""
        return self.consensus_engine.resolve(room_id, proposal)

    # ---- Knowledge Graph ----

    def add_knowledge_node(self, agent_id: str, knowledge: Dict) -> str:
        """Add knowledge node to evolving graph."""
        return self.graph_engine.add_node(agent_id, knowledge)

    def evolve_graph(self, agent_id: str, new_knowledge: Dict):
        """Evolve knowledge graph with new information."""
        self.graph_engine.evolve(agent_id, new_knowledge)

    def get_graph_state(self, agent_id: str) -> Optional[Dict]:
        """Get current knowledge graph state."""
        return self.graph_engine.get_state(agent_id)

    # ---- Trust System ----

    def record_interaction(self, from_agent: str, to_agent: str,
                           outcome: str, quality: float = 0.5):
        """Record agent interaction for trust scoring."""
        success = outcome.lower() in ("success", "completed", "passed", "ok")
        self.trust_manager.record_interaction(to_agent, success, outcome)

    def get_agent_reputation(self, agent_id: str) -> Optional[AgentReputation]:
        """Get agent reputation score."""
        return self.trust_manager.get_reputation(agent_id)

    def check_trust(self, agent_id: str, threshold: float = 0.5) -> bool:
        """Check if agent meets trust threshold."""
        return self.trust_manager.is_trusted(agent_id, threshold)

    # ---- Vault Integration ----

    def sync_vault(self, vault_path: str) -> Dict:
        """Sync with Obsidian vault."""
        return self.vault_integration.sync(vault_path)

    def load_vault_context(self, query: str = None) -> Dict:
        """Load context from vault."""
        return load_vault_context(self.vault_integration, query)

    # ---- Server Controls ----

    def start_a2a_server(self):
        """Start A2A server in background."""
        if self._a2a_server is None:
            from protocol_layer import ProtocolLayer
            protocol = ProtocolLayer()
            self._a2a_server = CoCommA2AServer(protocol, port=8021)
        self._a2a_server.start()

    def stop_a2a_server(self):
        """Stop A2A server."""
        if self._a2a_server:
            self._a2a_server.stop()

    def start_websocket(self):
        """Start WebSocket server."""
        if self._ws_server is None:
            self._ws_server = WebSocketServer(host="127.0.0.1", port=8022)
        self._ws_server.start()

    def stop_websocket(self):
        """Stop WebSocket server."""
        if self._ws_server:
            self._ws_server.stop()

    # ---- Status ----

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive CoComm integration status."""
        return {
            "initialized": self._initialized,
            "session": {
                "active": self.session_log.get_session().get("session_id", "none"),
                "tasks": len(self.session_log.get_session().get("tasks", []))
            },
            "memory": self.shared_memory.get_sync_status(),
            "agents": {
                "async_pool": self.async_pool.max_concurrent,
                "role_registry": len(self.role_registry.roles)
            },
            "servers": {
                "a2a": "running" if (self._a2a_server and self._a2a_server.running) else "stopped",
                "websocket": "running" if (self._ws_server and self._ws_server.running) else "stopped"
            }
        }


# Global instance
_cocomm_instance: Optional[CoCommIntegration] = None
_cocomm_lock = Lock()


def get_cocomm_integration(data_dir: Path = None) -> CoCommIntegration:
    """Get or create global CoComm integration instance."""
    global _cocomm_instance
    with _cocomm_lock:
        if _cocomm_instance is None:
            _cocomm_instance = CoCommIntegration(data_dir)
        return _cocomm_instance


def init_cocomm(data_dir: Path = None) -> CoCommIntegration:
    """Initialize CoComm integration."""
    return get_cocomm_integration(data_dir)


# Expose key classes for direct access
__all__ = [
    "CoCommIntegration",
    "get_cocomm_integration",
    "init_cocomm",
    # Re-export for convenience
    "ActiveSessionLog",
    "SharedMemory",
    "TriggerManager",
    "AgentConfigLoader",
    "RoleRegistry",
    "HandoffAgent",
    "AsyncAgentPool",
    "GoalDecomposer",
    "ConsensusEngine",
    "GraphEvolutionEngine",
    "TrustManager",
    "VaultIntegration",
]