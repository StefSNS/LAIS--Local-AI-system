"""
External AI Tool Integration - Register Claude Code, Codex, OpenCode as CoComm agents.
Enables cross-agent communication between LAIS and external AI tools.
"""

from typing import Dict, List, Optional, Callable
from pathlib import Path


class ExternalAIAgent:
    """Represents an external AI tool as a CoComm agent."""

    def __init__(self, agent_id: str, name: str, tool_type: str, 
                 command: str = None, capabilities: List[str] = None):
        self.agent_id = agent_id
        self.name = name
        self.tool_type = tool_type  # "claude_code", "codex", "opencode", "custom"
        self.command = command
        self.capabilities = capabilities or []
        self.online = False
        self.last_response = None

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "tool_type": self.tool_type,
            "command": self.command,
            "capabilities": self.capabilities,
            "online": self.online
        }


# Pre-configured external AI tool templates
EXTERNAL_TOOL_TEMPLATES = {
    "claude_code": {
        "name": "Claude Code",
        "capabilities": ["code", "edit", "shell", "git", "mcp", "subagent"],
        "command": "claude",
        "description": "Anthropic's CLI coding agent"
    },
    "codex": {
        "name": "Codex CLI", 
        "capabilities": ["code", "edit", "shell", "git", "sandbox"],
        "command": "codex",
        "description": "OpenAI's CLI coding agent"
    },
    "opencode": {
        "name": "OpenCode",
        "capabilities": ["code", "edit", "shell", "git", "mcp", "multi-provider"],
        "command": "opencode",
        "description": "Open-source CLI coding agent (75+ providers)"
    },
    "openclaw": {
        "name": "OpenClaw",
        "capabilities": ["email", "calendar", "memory", "automation", "web"],
        "command": "openclaw",
        "description": "Self-hosted personal AI assistant"
    },
    "jarvis": {
        "name": "JARVIS Mark XXXIX",
        "capabilities": ["voice", "vision", "search", "desktop", "messaging"],
        "command": "jarvis",
        "description": "Voice AI with security grid"
    },
    "gemini_cli": {
        "name": "Gemini CLI",
        "capabilities": ["code", "research", "multi-modal"],
        "command": "gemini",
        "description": "Google's CLI agent"
    }
}


def register_external_tool(protocol_layer, tool_type: str, 
                           custom_command: str = None,
                           custom_capabilities: List[str] = None) -> Optional[ExternalAIAgent]:
    """
    Register an external AI tool as a CoComm agent.
    
    Usage:
        from unified_layer.protocol_layer import ProtocolLayer
        from cocomm_tools import register_external_tool
        
        p = ProtocolLayer()
        agent = register_external_tool(p, "claude_code")
        print(f"Registered: {agent.name}")
    """
    template = EXTERNAL_TOOL_TEMPLATES.get(tool_type)
    if not template:
        return None
    
    agent = ExternalAIAgent(
        agent_id=f"ext_{tool_type}",
        name=template["name"],
        tool_type=tool_type,
        command=custom_command or template.get("command"),
        capabilities=custom_capabilities or template["capabilities"]
    )
    
    # Register in CoComm via protocol layer
    if hasattr(protocol_layer, 'cocomm') and protocol_layer.cocomm:
        protocol_layer.cocomm.assign_role(agent.agent_id, "specialist")
    
    # Also register in LAIS protocol layer as A2A agent
    protocol_layer.register_a2a_agent(
        name=agent.name,
        description=template["description"],
        capabilities=agent.capabilities,
        url=f"local://{agent.agent_id}"
    )
    
    # Store external agent reference
    if not hasattr(protocol_layer, '_external_agents'):
        protocol_layer._external_agents = {}
    protocol_layer._external_agents[agent.agent_id] = agent
    
    return agent


def register_all_external_tools(protocol_layer) -> Dict[str, ExternalAIAgent]:
    """Register all known external AI tools as agents."""
    registered = {}
    for tool_type in EXTERNAL_TOOL_TEMPLATES.keys():
        agent = register_external_tool(protocol_layer, tool_type)
        if agent:
            registered[tool_type] = agent
    return registered


def execute_via_external_tool(protocol_layer, tool_type: str, 
                              prompt: str, context: Dict = None) -> Optional[str]:
    """
    Execute a task via an external AI tool through CoComm.
    
    This routes the task to the external tool and returns the result.
    """
    template = EXTERNAL_TOOL_TEMPLATES.get(tool_type)
    if not template:
        return None
    
    agent_id = f"ext_{tool_type}"
    
    # Store task in shared memory for the external tool to pick up
    if hasattr(protocol_layer, 'cocomm') and protocol_layer.cocomm:
        protocol_layer.cocomm.store_memory(
            agent=agent_id,
            key="task",
            value=prompt,
            category="execution",
            priority="high"
        )
        
        if context:
            for k, v in context.items():
                protocol_layer.cocomm.store_memory(
                    agent=agent_id,
                    key=f"context_{k}",
                    value=str(v),
                    category="execution"
                )
    
    # Create A2A task for the external agent
    task = protocol_layer.delegate_task(
        from_agent="lais",
        to_agent=agent_id,
        task_type="execute",
        payload={"prompt": prompt, "context": context or {}},
        priority="normal"
    )
    
    return task.task_id


# Usage example for integration with different AI tools:
"""
# In your LAIS code:

from unified_layer.protocol_layer import ProtocolLayer
from cocomm_tools import register_external_tool, execute_via_external_tool

# Initialize
p = ProtocolLayer()

# Register external tools as CoComm agents
register_external_tool(p, "claude_code")
register_external_tool(p, "opencode")
register_external_tool(p, "jarvis")

# Now you can:
# 1. Route tasks to external tools
task_id = execute_via_external_tool(p, "claude_code", "Review my code for bugs")

# 2. Share memory between LAIS and external tools
p.cocomm_store_memory("lais", "project_context", "Working on API v2...")

# 3. Get results from external tools
results = p.cocomm_search_memory("project_context")

# 4. Coordinate via roles
p.cocomm_assign_role("ext_claude_code", "executor")
p.cocomm_assign_role("lais", "orchestrator")
"""

__all__ = [
    "ExternalAIAgent",
    "EXTERNAL_TOOL_TEMPLATES",
    "register_external_tool",
    "register_all_external_tools",
    "execute_via_external_tool"
]