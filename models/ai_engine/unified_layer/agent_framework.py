"""
Agent Framework - TypeScript-style agent definitions.
Based on Codebuff's .agents/ system.
"""

import json
import re
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock
import uuid

AGENTS_DIR = Path(__file__).resolve().parent.parent / ".agents"
AGENTS_TYPES_DIR = AGENTS_DIR / "types"
CUSTOM_AGENTS_DIR = AGENTS_DIR / "custom"


class AgentType(Enum):
    PROMPT = "prompt"
    PROGRAMMATIC = "programmatic"
    HYBRID = "hybrid"


@dataclass
class AgentToolDefinition:
    """Tool definition for agents."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCondition:
    """Condition for branching in programmatic agents."""
    field: str
    operator: str
    value: Any


@dataclass
class AgentStep:
    """A step in a programmatic agent."""
    tool: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    branch_on_result: Optional[str] = None


@dataclass
class AgentDefinition:
    """
    Agent definition (TypeScript-style from Codebuff).
    id: Unique identifier
    display_name: Human-readable name
    model: Model to use
    tool_names: Available tools
    instructions_prompt: Prompt for prompt-based agents
    agent_type: Type of agent (prompt, programmatic, hybrid)
    spawns_agents: List of agent IDs this agent can spawn
    conditions: Branching conditions for programmatic agents
    steps: Steps for programmatic agents
    """
    id: str
    display_name: str
    model: str = "default"
    tool_names: List[str] = field(default_factory=list)
    instructions_prompt: str = ""
    agent_type: AgentType = AgentType.PROMPT
    spawns_agents: List[str] = field(default_factory=list)
    conditions: List[AgentCondition] = field(default_factory=list)
    steps: List[AgentStep] = field(default_factory=list)
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "model": self.model,
            "tool_names": self.tool_names,
            "agent_type": self.agent_type.value,
            "spawns_agents": self.spawns_agents,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "usage_count": self.usage_count,
        }


class AgentRegistry:
    """
    Registry for agent definitions.
    Manages loading, creating, and executing agents.
    """

    def __init__(self):
        self.agents: Dict[str, AgentDefinition] = {}
        self.agent_handlers: Dict[str, Callable] = {}
        self.lock = Lock()
        self._ensure_directories()
        self._load_builtin_agents()

    def _ensure_directories(self):
        """Ensure agent directories exist."""
        AGENTS_DIR.mkdir(parents=True, exist_ok=True)
        AGENTS_TYPES_DIR.mkdir(parents=True, exist_ok=True)
        CUSTOM_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_builtin_agents(self):
        """Load built-in agents."""
        builtin = [
            AgentDefinition(
                id="base",
                display_name="Base Coding Agent",
                model="default",
                tool_names=["read", "edit", "write", "glob", "grep", "bash", "question"],
                instructions_prompt="You are a coding assistant that helps users write and modify code. Use the available tools to complete tasks.",
                agent_type=AgentType.PROMPT,
            ),
            AgentDefinition(
                id="git_committer",
                display_name="Git Committer",
                model="openai/gpt-5-nano",
                tool_names=["read", "run_terminal_command", "end_turn"],
                instructions_prompt="You create meaningful git commits by analyzing changes, reading relevant files for context, and crafting clear commit messages that explain the 'why' behind changes.",
                agent_type=AgentType.PROGRAMMATIC,
                steps=[
                    AgentStep(tool="run_terminal_command", parameters={"command": "git diff"}),
                    AgentStep(tool="run_terminal_command", parameters={"command": "git log --oneline -5"}),
                    AgentStep(tool="STEP_ALL"),
                ],
            ),
            AgentDefinition(
                id="code_reviewer",
                display_name="Code Reviewer",
                model="default",
                tool_names=["read", "grep", "bash", "question"],
                instructions_prompt="You review code for bugs, security issues, performance problems, and style violations. Provide constructive feedback.",
                agent_type=AgentType.PROMPT,
                spawns_agents=["base"],
            ),
            AgentDefinition(
                id="debugger",
                display_name="Debugger",
                model="default",
                tool_names=["read", "grep", "bash", "question"],
                instructions_prompt="You debug issues by analyzing errors, tracing code execution, and finding root causes. You systematically eliminate possibilities.",
                agent_type=AgentType.PROMPT,
            ),
        ]

        for agent in builtin:
            self.register(agent)

    def register(self, definition: AgentDefinition) -> None:
        """Register an agent definition."""
        self.agents[definition.id] = definition

    def unregister(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False

    def get(self, agent_id: str) -> Optional[AgentDefinition]:
        """Get an agent definition."""
        return self.agents.get(agent_id)

    def list(self, include_disabled: bool = False) -> List[Dict[str, Any]]:
        """List all registered agents."""
        return [
            agent.to_dict()
            for agent in self.agents.values()
            if include_disabled or agent.enabled
        ]

    def enable(self, agent_id: str) -> bool:
        """Enable an agent."""
        if agent_id in self.agents:
            self.agents[agent_id].enabled = True
            return True
        return False

    def disable(self, agent_id: str) -> bool:
        """Disable an agent."""
        if agent_id in self.agents:
            self.agents[agent_id].enabled = False
            return True
        return False

    def create_from_dict(self, data: Dict[str, Any]) -> AgentDefinition:
        """Create an agent definition from a dict."""
        steps = []
        if "steps" in data:
            for step_data in data["steps"]:
                steps.append(AgentStep(
                    tool=step_data.get("tool", ""),
                    parameters=step_data.get("parameters", {}),
                    branch_on_result=step_data.get("branch_on_result"),
                ))

        conditions = []
        if "conditions" in data:
            for cond_data in data["conditions"]:
                conditions.append(AgentCondition(
                    field=cond_data.get("field", ""),
                    operator=cond_data.get("operator", "=="),
                    value=cond_data.get("value"),
                ))

        return AgentDefinition(
            id=data.get("id", str(uuid.uuid4())[:8]),
            display_name=data.get("display_name", "Unnamed Agent"),
            model=data.get("model", "default"),
            tool_names=data.get("tool_names", []),
            instructions_prompt=data.get("instructions_prompt", ""),
            agent_type=AgentType(data.get("agent_type", "prompt")),
            spawns_agents=data.get("spawns_agents", []),
            conditions=conditions,
            steps=steps,
        )

    def save_to_file(self, agent_id: str, filepath: Optional[Path] = None) -> Dict[str, Any]:
        """Save an agent definition to a JSON file."""
        agent = self.get(agent_id)
        if not agent:
            return {"success": False, "error": f"Agent not found: {agent_id}"}

        filepath = filepath or (CUSTOM_AGENTS_DIR / f"{agent_id}.json")

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(agent.__dict__, f, indent=2, default=lambda x: x.__dict__ if hasattr(x, '__dict__') else str(x))
            return {"success": True, "path": str(filepath)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def load_from_file(self, filepath: Path) -> Dict[str, Any]:
        """Load an agent definition from a JSON file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            agent = self.create_from_dict(data)
            self.register(agent)
            return {"success": True, "agent": agent.to_dict()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def load_custom_agents(self) -> List[Dict[str, Any]]:
        """Load all custom agents from the custom agents directory."""
        loaded = []

        for filepath in CUSTOM_AGENTS_DIR.glob("*.json"):
            result = self.load_from_file(filepath)
            if result.get("success"):
                loaded.append(result["agent"])

        return loaded

    def render_prompt(self, agent_id: str, user_prompt: str, context: Dict[str, Any] = None) -> str:
        """Render the full prompt for an agent."""
        agent = self.get(agent_id)
        if not agent:
            return user_prompt

        context = context or {}

        prompt_parts = [
            f"# {agent.display_name}",
            "",
            agent.instructions_prompt,
            "",
        ]

        if context:
            prompt_parts.append("## Context")
            for key, value in context.items():
                prompt_parts.append(f"- {key}: {value}")
            prompt_parts.append("")

        prompt_parts.append(f"## Task")
        prompt_parts.append(user_prompt)

        return "\n".join(prompt_parts)

    def get_tools_for_agent(self, agent_id: str) -> List[str]:
        """Get the list of tool names for an agent."""
        agent = self.get(agent_id)
        if agent:
            return agent.tool_names
        return []


class AgentExecutor:
    """Executes agent tasks."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.execution_history: List[Dict[str, Any]] = []

    async def execute(
        self,
        agent_id: str,
        user_prompt: str,
        context: Dict[str, Any] = None,
        tool_handler: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Execute an agent task."""
        agent = self.registry.get(agent_id)
        if not agent:
            return {"success": False, "error": f"Agent not found: {agent_id}"}

        if not agent.enabled:
            return {"success": False, "error": f"Agent disabled: {agent_id}"}

        agent.usage_count += 1
        context = context or {}

        result = {
            "agent_id": agent_id,
            "prompt": user_prompt,
            "model": agent.model,
            "steps_executed": [],
        }

        if agent.agent_type == AgentType.PROGRAMMATIC or agent.agent_type == AgentType.HYBRID:
            for step in agent.steps:
                if step.tool == "STEP_ALL":
                    result["steps_executed"].append({"tool": "LLM", "status": "complete"})
                else:
                    step_result = {"tool": step.tool, "parameters": step.parameters}
                    if tool_handler:
                        try:
                            tool_result = await tool_handler(step.tool, step.parameters)
                            step_result["result"] = tool_result
                        except Exception as e:
                            step_result["error"] = str(e)
                    result["steps_executed"].append(step_result)

        result["success"] = True
        self.execution_history.append(result)
        return result

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all agents."""
        stats = {}
        for agent in self.registry.agents.values():
            stats[agent.id] = {
                "display_name": agent.display_name,
                "usage_count": agent.usage_count,
            }
        return stats


_registry_instance: Optional[AgentRegistry] = None
_executor_instance: Optional[AgentExecutor] = None


def get_agent_registry() -> AgentRegistry:
    """Get or create the agent registry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = AgentRegistry()
    return _registry_instance


def get_agent_executor() -> AgentExecutor:
    """Get or create the agent executor instance."""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = AgentExecutor(get_agent_registry())
    return _executor_instance


if __name__ == "__main__":
    registry = get_agent_registry()
    executor = get_agent_executor()

    print("=== Agent Framework ===")

    print("\n--- List Agents ---")
    for agent in registry.list():
        print(f"  [{agent['id']}] {agent['display_name']} (type: {agent['agent_type']})")

    print("\n--- Get Agent Tools ---")
    print(f"  base: {registry.get_tools_for_agent('base')}")
    print(f"  git_committer: {registry.get_tools_for_agent('git_committer')}")

    print("\n--- Render Prompt ---")
    prompt = registry.render_prompt(
        "code_reviewer",
        "Review the authentication module for security issues",
        {"project": "myapp", "language": "Python"}
    )
    print(prompt[:300])

    print("\n--- Usage Stats ---")
    print(json.dumps(executor.get_usage_stats(), indent=2))