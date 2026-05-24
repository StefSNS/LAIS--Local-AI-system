"""
Memory Tools - Provides memory and session_search tools for the agent.
Based on Hermes Agent's tool design.
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path

from knowledge.memory.hermes_memory import get_hermes_memory, HermesMemory
from knowledge.memory.session_search import get_session_search, SessionSearch


class MemoryTool:
    """
    Tool for managing Hermes-style dual memory (MEMORY.md + USER.md).
    Actions: add, replace, remove
    """

    def __init__(self):
        self.memory = get_hermes_memory()

    def execute(self, action: str, target: str = "memory", content: str = "",
                old_text: str = "") -> Dict[str, Any]:
        """
        Execute a memory action.

        Args:
            action: "add", "replace", or "remove"
            target: "memory" (agent notes) or "user" (user profile)
            content: For add/replace - the content to add/replace to
            old_text: For replace/remove - substring to match

        Returns:
            Dict with success status and details
        """
        if action == "add":
            if not content:
                return {"success": False, "error": "content required for add"}
            return self.memory.add(content, target)

        elif action == "replace":
            if not old_text or not content:
                return {"success": False, "error": "old_text and content required for replace"}
            return self.memory.replace(old_text, content, target)

        elif action == "remove":
            if not old_text:
                return {"success": False, "error": "old_text required for remove"}
            return self.memory.remove(old_text, target)

        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def get_status(self) -> Dict[str, Any]:
        """Get memory status."""
        return self.memory.get_status()

    def render_for_prompt(self) -> str:
        """Get memory content formatted for system prompt."""
        return self.memory.render_for_prompt()


class SessionSearchTool:
    """
    Tool for searching past conversations using FTS5.
    """

    def __init__(self):
        self.search = get_session_search()

    def execute(self, action: str, query: str = "", session_id: str = "",
                agent: str = "opencode", max_results: int = 10,
                limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Execute a session search action.

        Actions:
            - search: Search all messages (query required)
            - get: Get specific session (session_id required)
            - list: List recent sessions
            - messages: Get messages from a session
        """
        if action == "search":
            if not query:
                return {"success": False, "error": "query required for search"}
            results = self.search.search(query, agent, max_results)
            return {"success": True, "results": results, "count": len(results)}

        elif action == "get":
            if not session_id:
                return {"success": False, "error": "session_id required"}
            session = self.search.get_session(session_id)
            if session:
                return {"success": True, "session": session}
            return {"success": False, "error": f"Session not found: {session_id}"}

        elif action == "list":
            sessions = self.search.list_sessions(agent, limit)
            return {"success": True, "sessions": sessions, "count": len(sessions)}

        elif action == "messages":
            if not session_id:
                return {"success": False, "error": "session_id required"}
            messages = self.search.get_session_messages(session_id, limit, offset)
            return {"success": True, "messages": messages, "count": len(messages)}

        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def get_stats(self) -> Dict[str, Any]:
        """Get session database stats."""
        return self.search.get_stats()


_memory_tool_instance: Optional[MemoryTool] = None
_session_search_tool_instance: Optional[SessionSearchTool] = None


def get_memory_tool() -> MemoryTool:
    """Get or create the memory tool instance."""
    global _memory_tool_instance
    if _memory_tool_instance is None:
        _memory_tool_instance = MemoryTool()
    return _memory_tool_instance


def get_session_search_tool() -> SessionSearchTool:
    """Get or create the session search tool instance."""
    global _session_search_tool_instance
    if _session_search_tool_instance is None:
        _session_search_tool_instance = SessionSearchTool()
    return _session_search_tool_instance


if __name__ == "__main__":
    print("=== Memory Tool Test ===")
    mt = get_memory_tool()

    print("\n--- Add Memory ---")
    print(mt.execute("add", "memory", "User prefers TypeScript over JavaScript"))

    print("\n--- Add User ---")
    print(mt.execute("add", "user", "Stef is a software developer, works on AI projects"))

    print("\n--- Status ---")
    print(json.dumps(mt.get_status(), indent=2))

    print("\n--- Render for Prompt ---")
    print(mt.render_for_prompt())

    print("\n=== Session Search Tool Test ===")
    sst = get_session_search_tool()

    print("\n--- Start Session ---")
    sst.search.start_session("test_session", "opencode", "minimax")

    print("\n--- Log Messages ---")
    sst.search.log_message("test_session", "user", "Let's build a new feature")
    sst.search.log_message("test_session", "assistant", "I'll use the brainstorming skill")

    print("\n--- Search ---")
    print(json.dumps(sst.execute("search", query="brainstorming feature"), indent=2))

    print("\n--- List Sessions ---")
    print(json.dumps(sst.execute("list", limit=5), indent=2))

    print("\n--- Stats ---")
    print(json.dumps(sst.get_stats(), indent=2))