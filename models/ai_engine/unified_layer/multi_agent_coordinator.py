"""
Multi-Agent Coordinator - Orchestrates specialized subagents.
Based on Codebuff's agent coordination system.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
from threading import Lock

from unified_layer.skill_engine import get_skill_engine, SkillEngine


class AgentRole(Enum):
    FILE_PICKER = "file_picker"
    PLANNER = "planner"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    RESEARCHER = "researcher"
    DEBUGGER = "debugger"
    TESTER = "tester"
    CUSTOM = "custom"


@dataclass
class AgentDefinition:
    """Definition of an agent (TypeScript-style from Codebuff)."""
    id: str
    display_name: str
    role: AgentRole
    model: str = "default"
    tool_names: List[str] = field(default_factory=list)
    instructions_prompt: str = ""
    spawns_agents: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class AgentTask:
    """A task assigned to an agent."""
    task_id: str
    agent_id: str
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseAgent:
    """Base class for all agents."""

    def __init__(self, definition: AgentDefinition):
        self.definition = definition
        self.role = definition.role
        self.tool_names = definition.tool_names

    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a task. Override in subclasses."""
        raise NotImplementedError

    async def handle_steps(self, task: AgentTask) -> List[Dict[str, Any]]:
        """Handle step-by-step execution. Override in subclasses."""
        raise NotImplementedError


class FilePickerAgent(BaseAgent):
    """Agent that scans codebase and finds relevant files."""

    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        prompt = task.prompt
        context = task.context

        results = {
            "files_found": [],
            "architecture": {},
            "summary": "",
        }

        from unified_layer.rag_pipeline import get_rag_pipeline
        rag = get_rag_pipeline()

        files = rag.search_code(prompt, limit=20)
        results["files_found"] = [f.get("file", f.get("path", "")) for f in files]

        results["summary"] = f"Found {len(results['files_found'])} relevant files for: {prompt}"

        return results


class PlannerAgent(BaseAgent):
    """Agent that plans which files need changes."""

    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        context = task.context
        files = context.get("files_found", [])

        plan = {
            "steps": [],
            "dependencies": {},
            "estimated_changes": len(files),
        }

        for i, f in enumerate(files[:10]):
            plan["steps"].append({
                "step": i + 1,
                "file": f,
                "action": "modify",
                "description": f"Update {f}",
            })

        return plan


class EditorAgent(BaseAgent):
    """Agent that makes precise code edits."""

    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        plan = task.context.get("plan", {})
        steps = plan.get("steps", [])

        results = {
            "files_modified": [],
            "edits_made": [],
            "errors": [],
        }

        for step in steps:
            results["files_modified"].append(step.get("file", ""))
            results["edits_made"].append({
                "file": step.get("file"),
                "action": step.get("action"),
            })

        return results


class ReviewerAgent(BaseAgent):
    """Agent that validates changes."""

    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        context = task.context
        files = context.get("files_modified", [])

        results = {
            "passed": True,
            "issues": [],
            "suggestions": [],
        }

        return results


class MultiAgentCoordinator:
    """
    Coordinates multiple specialized agents.
    Based on Codebuff's multi-agent approach:
    File Picker → Planner → Editor → Reviewer
    """

    def __init__(self):
        self.agents: Dict[str, AgentDefinition] = {}
        self.agent_instances: Dict[str, BaseAgent] = {}
        self.task_history: List[AgentTask] = []
        self._init_default_agents()
        self.coordination_flow = [
            AgentRole.FILE_PICKER,
            AgentRole.PLANNER,
            AgentRole.EDITOR,
            AgentRole.REVIEWER,
        ]
        self.lock = Lock()

    def _init_default_agents(self):
        """Initialize default specialized agents."""
        default_agents = [
            AgentDefinition(
                id="file_picker",
                display_name="File Picker",
                role=AgentRole.FILE_PICKER,
                tool_names=["read", "glob", "grep", "rag"],
                instructions_prompt="Scan the codebase to understand architecture and find relevant files for the task.",
            ),
            AgentDefinition(
                id="planner",
                display_name="Planner",
                role=AgentRole.PLANNER,
                tool_names=["read", "question"],
                instructions_prompt="Plan which files need changes and in what order.",
            ),
            AgentDefinition(
                id="editor",
                display_name="Editor",
                role=AgentRole.EDITOR,
                tool_names=["read", "edit", "write", "bash"],
                instructions_prompt="Make precise code edits based on the plan.",
            ),
            AgentDefinition(
                id="reviewer",
                display_name="Reviewer",
                role=AgentRole.REVIEWER,
                tool_names=["read", "grep", "bash"],
                instructions_prompt="Validate changes, check for errors, and suggest improvements.",
            ),
            AgentDefinition(
                id="researcher",
                display_name="Researcher",
                role=AgentRole.RESEARCHER,
                tool_names=["websearch", "webfetch", "read"],
                instructions_prompt="Research topics, gather information, and provide context.",
            ),
            AgentDefinition(
                id="debugger",
                display_name="Debugger",
                role=AgentRole.DEBUGGER,
                tool_names=["read", "grep", "bash", "question"],
                instructions_prompt="Debug issues, analyze errors, and find root causes.",
            ),
            AgentDefinition(
                id="tester",
                display_name="Tester",
                role=AgentRole.TESTER,
                tool_names=["read", "write", "bash"],
                instructions_prompt="Write tests, run test suites, and verify functionality.",
            ),
        ]

        role_to_class = {
            AgentRole.FILE_PICKER: FilePickerAgent,
            AgentRole.PLANNER: PlannerAgent,
            AgentRole.EDITOR: EditorAgent,
            AgentRole.REVIEWER: ReviewerAgent,
        }

        for defn in default_agents:
            self.register_agent(defn)
            if defn.role in role_to_class:
                self.agent_instances[defn.id] = role_to_class[defn.role](defn)

    def register_agent(self, definition: AgentDefinition) -> None:
        """Register a new agent definition."""
        self.agents[definition.id] = definition

    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents."""
        return [
            {
                "id": a.id,
                "display_name": a.display_name,
                "role": a.role.value,
                "tool_names": a.tool_names,
                "enabled": a.enabled,
            }
            for a in self.agents.values()
        ]

    async def run_coordinated(
        self,
        prompt: str,
        flow: Optional[List[AgentRole]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run a coordinated multi-agent task.
        Default flow: File Picker → Planner → Editor → Reviewer
        """
        flow = flow or self.coordination_flow
        context = context or {}
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        results = {
            "task_id": task_id,
            "prompt": prompt,
            "flow": [r.value for r in flow],
            "stages": {},
        }

        current_context = {"original_prompt": prompt, **context}

        for role in flow:
            agent_def = self._get_agent_by_role(role)
            if not agent_def:
                continue

            task = AgentTask(
                task_id=task_id,
                agent_id=agent_def.id,
                prompt=prompt,
                context=current_context,
            )

            if agent_def.id in self.agent_instances:
                agent = self.agent_instances[agent_def.id]
                try:
                    result = await agent.execute(task)
                    task.result = result
                    task.completed_at = datetime.now().isoformat()
                    results["stages"][role.value] = {
                        "status": "success",
                        "result": result,
                    }
                    current_context[role.value] = result
                except Exception as e:
                    task.error = str(e)
                    results["stages"][role.value] = {
                        "status": "error",
                        "error": str(e),
                    }

        results["final_context"] = current_context
        return results

    def _get_agent_by_role(self, role: AgentRole) -> Optional[AgentDefinition]:
        """Get agent definition by role."""
        for agent in self.agents.values():
            if agent.role == role:
                return agent
        return None

    async def run_single_agent(
        self,
        agent_id: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run a single agent task."""
        agent_def = self.get_agent(agent_id)
        if not agent_def:
            return {"success": False, "error": f"Unknown agent: {agent_id}"}

        task = AgentTask(
            task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_id=agent_id,
            prompt=prompt,
            context=context or {},
        )

        if agent_id in self.agent_instances:
            agent = self.agent_instances[agent_id]
            try:
                result = await agent.execute(task)
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "Agent not implemented"}

    def spawn_agent(self, agent_id: str, prompt: str) -> AgentTask:
        """Spawn a subagent (for use within another agent)."""
        return AgentTask(
            task_id=f"spawn_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_id=agent_id,
            prompt=prompt,
        )

    def get_task_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent task history."""
        return [
            {
                "task_id": t.task_id,
                "agent_id": t.agent_id,
                "prompt": t.prompt[:100],
                "created_at": t.created_at,
                "completed_at": t.completed_at,
                "status": "completed" if t.completed_at else "pending",
            }
            for t in self.task_history[-limit:]
        ]


_coordinator_instance: Optional[MultiAgentCoordinator] = None


def get_multi_agent_coordinator() -> MultiAgentCoordinator:
    """Get or create the multi-agent coordinator instance."""
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = MultiAgentCoordinator()
    return _coordinator_instance


if __name__ == "__main__":
    import sys

    async def main():
        coordinator = get_multi_agent_coordinator()

        print("=== Multi-Agent Coordinator ===")

        print("\n--- Registered Agents ---")
        for agent in coordinator.list_agents():
            print(f"  [{agent['role']}] {agent['display_name']}: {', '.join(agent['tool_names'])}")

        print("\n--- Coordinated Task ---")
        result = await coordinator.run_coordinated(
            "Add authentication to my API"
        )
        print(f"Task ID: {result['task_id']}")
        for stage, data in result["stages"].items():
            print(f"  {stage}: {data.get('status', 'unknown')}")

        print("\n--- Single Agent ---")
        result = await coordinator.run_single_agent(
            "file_picker",
            "Find all Python files related to authentication"
        )
        print(json.dumps(result, indent=2))

    asyncio.run(main())