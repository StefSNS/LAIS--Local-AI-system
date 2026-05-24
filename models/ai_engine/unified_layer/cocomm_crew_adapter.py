"""CrewAI-compatible adapter on top of CoComm's MultiAgentCoordinator.
Ports 3 CrewAI patterns: Crew.kickoff(), @tool decorator, structured output."""

import json
from typing import List, Dict, Any, Optional, Callable, Type
from functools import wraps
from pydantic import BaseModel


_tool_registry: Dict[str, Dict] = {}


def tool(name: Optional[str] = None, description: str = ""):
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        _tool_registry[tool_name] = {"fn": func, "description": description or func.__doc__ or "", "name": tool_name}

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_tools() -> Dict[str, Dict]:
    return dict(_tool_registry)


class CrewAgent:
    def __init__(self, role: str, goal: str, backstory: str = "", tools: Optional[List[Callable]] = None,
                 allow_delegation: bool = False, verbose: bool = False):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools or []
        self.allow_delegation = allow_delegation
        self.verbose = verbose

    def to_def(self) -> dict:
        return {
            "name": self.role.lower().replace(" ", "_"),
            "role": self.role,
            "goal": self.goal,
            "backstory": self.backstory,
            "tools": [t.__name__ if hasattr(t, "__name__") else str(t) for t in self.tools],
            "allow_delegation": self.allow_delegation,
        }


class CrewTask:
    def __init__(self, description: str, agent: CrewAgent,
                 expected_output: str = "",
                 output_pydantic: Optional[Type[BaseModel]] = None,
                 context: Optional[List["CrewTask"]] = None):
        self.description = description
        self.agent = agent
        self.expected_output = expected_output
        self.output_pydantic = output_pydantic
        self.context = context or []

    def to_def(self) -> dict:
        return {
            "description": self.description,
            "agent": self.agent.role,
            "expected_output": self.expected_output,
        }


class CrewResult:
    def __init__(self, tasks_output: List[Dict[str, Any]]):
        self.tasks_output = tasks_output

    @property
    def raw(self) -> str:
        return json.dumps(self.tasks_output[-1]) if self.tasks_output else ""

    def __str__(self) -> str:
        return self.raw


class Crew:
    def __init__(self, agents: List[CrewAgent], tasks: List[CrewTask],
                 verbose: bool = False, max_rpm: Optional[int] = None):
        self.agents = agents
        self.tasks = tasks
        self.verbose = verbose
        self.max_rpm = max_rpm
        self._coordinator = None

    def _get_coordinator(self):
        if self._coordinator is None:
            from unified_layer.multi_agent_coordinator import get_multi_agent_coordinator
            self._coordinator = get_multi_agent_coordinator()
        return self._coordinator

    def kickoff(self, inputs: Optional[Dict[str, Any]] = None) -> CrewResult:
        coord = self._get_coordinator()
        available_tools = get_tools()
        outputs = []
        for agent_def in self.agents:
            tools_for_agent = [available_tools[t.__name__] for t in agent_def.tools
                              if t.__name__ in available_tools]
            agent_data = agent_def.to_def()
            agent_data["tools"] = tools_for_agent
            try:
                coord.register_agent(agent_data["name"], agent_data["role"],
                                     agent_data.get("goal", ""),
                                     tools=[t["name"] for t in tools_for_agent])
            except Exception:
                pass
        for task in self.tasks:
            task_def = task.to_def()
            agent_name = task.agent.role.lower().replace(" ", "_")
            prompt = task_def["description"]
            if inputs:
                for k, v in inputs.items():
                    prompt = prompt.replace(f"{{{k}}}", str(v))
            if task.context:
                ctx = "\n".join(f"- {c.description}: {c.to_def()['description']}" for c in task.context)
                prompt = f"{prompt}\n\nContext:\n{ctx}"
            result = coord.run_agent_task(agent_name, prompt)
            task_output = {"agent": task.agent.role, "task": task.description, "result": str(result)}
            if task.output_pydantic:
                try:
                    task_output["parsed"] = task.output_pydantic.model_validate_json(str(result)).model_dump()
                except Exception:
                    task_output["parsed"] = None
            outputs.append(task_output)
        return CrewResult(outputs)
