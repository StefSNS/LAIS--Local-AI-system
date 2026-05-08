"""
Tool Calling Framework v1.0 - Unified declarative tool schemas.
Standardizes tool use across all agents with OpenAI-compatible format.
Automatic parsing, validation, execution, and result injection.
"""

from datetime import datetime
from typing import Any, Callable, Optional
from threading import Lock
import json
import inspect


class ToolParameter:
    """Defines a single tool parameter."""

    def __init__(
        self,
        name: str,
        param_type: str,
        description: str,
        required: bool = False,
        enum: Optional[list] = None,
        default: Any = None,
    ):
        self.name = name
        self.param_type = param_type
        self.description = description
        self.required = required
        self.enum = enum
        self.default = default

    def to_schema(self) -> dict:
        schema = {"type": self.param_type, "description": self.description}
        if self.enum:
            schema["enum"] = self.enum
        return schema


class ToolDefinition:
    """Declarative definition of a callable tool."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: list[ToolParameter],
        handler: Callable,
        category: str = "general",
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.category = category
        self.call_count = 0
        self.last_called: Optional[datetime] = None
        self.total_latency_ms = 0.0

    def to_openai_format(self) -> dict:
        properties = {}
        required = []
        for p in self.parameters:
            properties[p.name] = p.to_schema()
            if p.required:
                required.append(p.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def validate_args(self, args: dict) -> tuple[bool, Optional[str]]:
        """Validate arguments against parameter schema."""
        for p in self.parameters:
            if p.required and p.name not in args:
                return False, f"Missing required parameter: {p.name}"

            if p.name in args and p.enum:
                if args[p.name] not in p.enum:
                    return False, f"Invalid value for {p.name}: {args[p.name]}. Must be one of {p.enum}"

        return True, None

    def execute(self, args: dict) -> dict:
        """Execute tool with validated arguments."""
        import time
        start = time.time()

        try:
            result = self.handler(**args)
            latency_ms = (time.time() - start) * 1000
            self.call_count += 1
            self.last_called = datetime.now()
            self.total_latency_ms += latency_ms

            return {
                "success": True,
                "result": result,
                "latency_ms": round(latency_ms, 2),
                "error": None,
            }
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            return {
                "success": False,
                "result": None,
                "latency_ms": round(latency_ms, 2),
                "error": str(e),
            }


class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self):
        self._tools = {}
        self._lock = Lock()

    def register(self, tool: ToolDefinition) -> None:
        with self._lock:
            self._tools[tool.name] = tool

    def register_many(self, tools: list[ToolDefinition]) -> None:
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "parameters": [p.name for p in t.parameters],
                "call_count": t.call_count,
            }
            for t in self._tools.values()
        ]

    def get_all_schemas(self) -> list[dict]:
        return [t.to_openai_format() for t in self._tools.values()]

    def get_by_category(self, category: str) -> list[ToolDefinition]:
        return [t for t in self._tools.values() if t.category == category]

    def remove(self, name: str) -> bool:
        with self._lock:
            if name in self._tools:
                del self._tools[name]
                return True
        return False


class ToolCallParser:
    """Parse LLM tool calls from various formats."""

    @staticmethod
    def parse_tool_call(text: str) -> Optional[dict]:
        """Extract tool call from LLM response text."""
        text = text.strip()

        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        try:
            data = json.loads(text)
            if "name" in data and "arguments" in data:
                return data
            if "tool" in data and "parameters" in data:
                return {"name": data["tool"], "arguments": data["parameters"]}
            if "function" in data:
                return {"name": data["function"]["name"], "arguments": data["function"]["arguments"]}
        except Exception:
            pass

        import re
        pattern = r'["\']name["\']\s*:\s*["\']([^"\']+)["\']'
        match = re.search(pattern, text)
        if match:
            tool_name = match.group(1)
            args_pattern = r'["\']arguments["\']\s*:\s*(\{[^}]+\})'
            args_match = re.search(args_pattern, text)
            if args_match:
                try:
                    args = json.loads(args_match.group(1))
                    return {"name": tool_name, "arguments": args}
                except Exception:
                    pass

        return None


class ToolCallingEngine:
    """
    End-to-end tool calling: parse LLM output → validate → execute → format result.
    """

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or ToolRegistry()
        self.parser = ToolCallParser()
        self._execution_log = []
        self._lock = Lock()

    def process_response(
        self,
        llm_response: str,
        auto_execute: bool = True,
    ) -> dict:
        """
        Process LLM response for tool calls.

        Args:
            llm_response: Raw LLM output
            auto_execute: Whether to automatically execute found tool calls

        Returns:
            Dict with tool call info and execution result
        """
        tool_call = self.parser.parse_tool_call(llm_response)
        if not tool_call:
            return {
                "has_tool_call": False,
                "tool_name": None,
                "arguments": None,
                "execution_result": None,
                "text_response": llm_response,
            }

        tool_name = tool_call["name"]
        arguments = tool_call.get("arguments", {})
        execution_result = None

        if auto_execute:
            execution_result = self.execute_tool(tool_name, arguments)

        return {
            "has_tool_call": True,
            "tool_name": tool_name,
            "arguments": arguments,
            "execution_result": execution_result,
            "text_response": llm_response,
        }

    def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """Execute a registered tool by name."""
        tool = self.registry.get(tool_name)
        if not tool:
            result = {
                "success": False,
                "result": None,
                "error": f"Tool '{tool_name}' not found",
            }
        else:
            valid, error = tool.validate_args(arguments)
            if not valid:
                result = {"success": False, "result": None, "error": error}
            else:
                result = tool.execute(arguments)

        self._log_execution(tool_name, arguments, result)
        return result

    def format_result_for_llm(self, execution_result: dict, tool_name: str) -> str:
        """Format execution result as LLM-readable string."""
        if execution_result.get("success"):
            result = execution_result["result"]
            if isinstance(result, dict):
                return json.dumps(result, indent=2)
            return str(result)
        return f"Error executing {tool_name}: {execution_result.get('error', 'Unknown error')}"

    def build_context_with_tools(
        self,
        user_query: str,
        available_tools: Optional[list[str]] = None,
    ) -> str:
        """Build a prompt that includes available tool definitions."""
        if available_tools:
            tools = [t for t in self.registry._tools.values() if t.name in available_tools]
        else:
            tools = list(self.registry._tools.values())

        tool_descriptions = []
        for tool in tools:
            params = ", ".join(p.name for p in tool.parameters)
            tool_descriptions.append(
                f"- {tool.name}({params}): {tool.description}"
            )

        tools_text = "\n".join(tool_descriptions)

        return f"""You have access to the following tools:

{tools_text}

To use a tool, respond with a JSON object:
```json
{{
  "name": "tool_name",
  "arguments": {{"param1": "value1", "param2": "value2"}}
}}
```

User query: {user_query}"""

    def get_execution_stats(self) -> dict:
        with self._lock:
            if not self._execution_log:
                return {"total_calls": 0}

            tool_counts = {}
            for entry in self._execution_log:
                name = entry["tool_name"]
                tool_counts[name] = tool_counts.get(name, 0) + 1

            success_rate = sum(1 for e in self._execution_log if e.get("success")) / len(self._execution_log)

            return {
                "total_calls": len(self._execution_log),
                "tool_usage": tool_counts,
                "success_rate": round(success_rate * 100, 1),
            }

    def _log_execution(self, tool_name: str, arguments: dict, result: dict) -> None:
        entry = {
            "tool_name": tool_name,
            "arguments": arguments,
            "success": result.get("success", False),
            "latency_ms": result.get("latency_ms", 0),
            "timestamp": datetime.now().isoformat(),
        }
        with self._lock:
            self._execution_log.append(entry)


_global_engine: Optional[ToolCallingEngine] = None
_engine_lock = Lock()


def get_tool_engine() -> ToolCallingEngine:
    global _global_engine
    if _global_engine is None:
        with _engine_lock:
            if _global_engine is None:
                _global_engine = ToolCallingEngine()
    return _global_engine
