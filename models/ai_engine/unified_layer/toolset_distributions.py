"""
Toolset Distributions - Modular tool groupings with toggleable sets.
Based on Hermes Agent's toolsets system.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from threading import Lock
from dataclasses import dataclass, field

TOOLSETS_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "toolsets"
TOOLSETS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = TOOLSETS_DIR / "toolset_config.json"
LOCK = Lock()


@dataclass
class ToolDefinition:
    """Definition of a single tool."""
    name: str
    description: str
    category: str
    requires_permission: bool = False
    risky: bool = False
    aliases: List[str] = field(default_factory=list)


@dataclass
class Toolset:
    """A named collection of tools."""
    name: str
    description: str
    tools: List[str]
    enabled: bool = True
    required_permissions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class ToolsetDistributions:
    """
    Manages modular tool groupings that can be toggled on/off.
    Similar to Hermes Agent's toolset distributions.
    """

    DEFAULT_TOOLSETS = {
        "core": {
            "description": "Essential read operations",
            "tools": ["read", "glob", "grep", "webfetch", "question"],
            "tags": ["essential", "safe"],
        },
        "code": {
            "description": "Code reading and analysis",
            "tools": ["read", "glob", "grep", "bash"],
            "tags": ["development", "safe"],
        },
        "edit": {
            "description": "File editing capabilities",
            "tools": ["edit", "write"],
            "tags": ["development", "write"],
            "required_permissions": ["file_write"],
        },
        "bash": {
            "description": "Shell command execution",
            "tools": ["bash"],
            "tags": ["development", "shell"],
            "required_permissions": ["shell"],
            "risky_tools": ["bash"],
        },
        "web": {
            "description": "Web search and fetch",
            "tools": ["websearch", "webfetch"],
            "tags": ["research", "safe"],
        },
        "memory": {
            "description": "Memory and session management",
            "tools": ["memory", "session_search"],
            "tags": ["memory", "safe"],
        },
        "skills": {
            "description": "Skill loading and management",
            "tools": ["skill"],
            "tags": ["skills", "safe"],
        },
        "planning": {
            "description": "Planning and task management",
            "tools": ["write", "read", "question"],
            "tags": ["planning", "safe"],
        },
        "debugging": {
            "description": "Debug and test tools",
            "tools": ["grep", "read", "bash", "question"],
            "tags": ["debug", "safe"],
        },
        "security": {
            "description": "Security analysis tools",
            "tools": ["read", "grep", "question"],
            "tags": ["security", "safe"],
        },
    }

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.toolsets: Dict[str, Toolset] = {}
        self.enabled_toolsets: Set[str] = set()
        self._load_config()
        self._init_default_toolsets()

    def _load_config(self):
        """Load toolset configuration."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {"enabled_toolsets": ["core", "code", "memory"]}
        else:
            self.config = {"enabled_toolsets": ["core", "code", "memory"]}
            self._save_config()

    def _save_config(self):
        """Save toolset configuration."""
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def _init_default_toolsets(self):
        """Initialize default toolsets."""
        for name, data in self.DEFAULT_TOOLSETS.items():
            self.toolsets[name] = Toolset(
                name=name,
                description=data["description"],
                tools=data["tools"],
                required_permissions=data.get("required_permissions", []),
                tags=data.get("tags", []),
            )

        self.enabled_toolsets = set(self.config.get("enabled_toolsets", []))

    def register_tool(self, tool: ToolDefinition) -> None:
        """Register a tool definition."""
        self.tools[tool.name] = tool

    def register_tools(self, tools: List[ToolDefinition]) -> None:
        """Register multiple tools."""
        for tool in tools:
            self.register_tool(tool)

    def create_toolset(self, name: str, description: str, tools: List[str],
                       tags: List[str] = None, required_permissions: List[str] = None) -> bool:
        """Create a new toolset."""
        if name in self.toolsets:
            return False

        self.toolsets[name] = Toolset(
            name=name,
            description=description,
            tools=tools,
            tags=tags or [],
            required_permissions=required_permissions or [],
        )
        return True

    def update_toolset(self, name: str, tools: List[str] = None, description: str = None) -> bool:
        """Update an existing toolset."""
        if name not in self.toolsets:
            return False

        if tools is not None:
            self.toolsets[name].tools = tools
        if description is not None:
            self.toolsets[name].description = description
        return True

    def delete_toolset(self, name: str) -> bool:
        """Delete a toolset."""
        if name not in self.toolsets:
            return False
        if name in self.enabled_toolsets:
            self.enabled_toolsets.remove(name)
        del self.toolsets[name]
        return True

    def enable_toolset(self, name: str) -> Dict[str, Any]:
        """Enable a toolset."""
        if name not in self.toolsets:
            return {"success": False, "error": f"Unknown toolset: {name}"}

        self.enabled_toolsets.add(name)
        self.config["enabled_toolsets"] = list(self.enabled_toolsets)
        self._save_config()

        return {"success": True, "toolset": name}

    def disable_toolset(self, name: str) -> Dict[str, Any]:
        """Disable a toolset."""
        if name not in self.toolsets:
            return {"success": False, "error": f"Unknown toolset: {name}"}

        if name in self.enabled_toolsets:
            self.enabled_toolsets.remove(name)
            self.config["enabled_toolsets"] = list(self.enabled_toolsets)
            self._save_config()

        return {"success": True, "toolset": name}

    def get_available_tools(self) -> List[str]:
        """Get list of all available tools from enabled toolsets."""
        tools = set()
        for name in self.enabled_toolsets:
            if name in self.toolsets:
                tools.update(self.toolsets[name].tools)
        return list(tools)

    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available in any enabled toolset."""
        for name in self.enabled_toolsets:
            if name in self.toolsets:
                if tool_name in self.toolsets[name].tools:
                    return True

        for name, ts in self.toolsets.items():
            if tool_name in ts.aliases:
                return name in self.enabled_toolsets

        return False

    def get_toolsets_info(self) -> List[Dict[str, Any]]:
        """Get info about all toolsets."""
        return [
            {
                "name": ts.name,
                "description": ts.description,
                "tools": ts.tools,
                "enabled": ts.name in self.enabled_toolsets,
                "tags": ts.tags,
                "required_permissions": ts.required_permissions,
            }
            for ts in self.toolsets.values()
        ]

    def get_tool_details(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get details about a specific tool."""
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            return {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "requires_permission": tool.requires_permission,
                "risky": tool.risky,
            }

        for ts in self.toolsets.values():
            if tool_name in ts.tools:
                return {
                    "name": tool_name,
                    "available_in": ts.name,
                    "toolset_enabled": ts.name in self.enabled_toolsets,
                }

        return None

    def get_risky_tools(self) -> List[str]:
        """Get list of tools marked as risky."""
        risky = []
        for ts in self.toolsets.values():
            if ts.name in self.enabled_toolsets:
                risky.extend(ts.tools)
        return list(set(risky))


_toolset_instance: Optional[ToolsetDistributions] = None


def get_toolset_distributions() -> ToolsetDistributions:
    """Get or create the toolset distributions instance."""
    global _toolset_instance
    if _toolset_instance is None:
        _toolset_instance = ToolsetDistributions()
    return _toolset_instance


if __name__ == "__main__":
    td = get_toolset_distributions()

    print("=== Toolset Distributions ===")

    print("\n--- All Toolsets ---")
    for ts in td.get_toolsets_info():
        status = "ENABLED" if ts["enabled"] else "disabled"
        print(f"  [{status}] {ts['name']}: {ts['description']}")
        print(f"         Tools: {', '.join(ts['tools'])}")

    print("\n--- Available Tools ---")
    print(f"  {td.get_available_tools()}")

    print("\n--- Test: Tool Availability ---")
    for tool in ["read", "bash", "edit", "websearch"]:
        print(f"  {tool}: {td.is_tool_available(tool)}")

    print("\n--- Test: Enable/Disable ---")
    print(td.enable_toolset("edit"))
    print(td.disable_toolset("bash"))

    print("\n--- Available After Changes ---")
    print(f"  {td.get_available_tools()}")