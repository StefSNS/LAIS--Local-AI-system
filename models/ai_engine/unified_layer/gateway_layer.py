"""
Gateway Layer - Phase 6 of Architecture Evolution
Unified channel routing for agent communication.
Multi-channel support documented for future implementation.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from threading import Lock

CHANNEL_LOG_FILE = Path(
    r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\memory\channel_log.json"
)
CHANNEL_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
LOCK = Lock()


class Channel:
    """Represents a communication channel."""

    def __init__(
        self,
        channel_id: str,
        name: str,
        channel_type: str,
        agent: str,
        config: Optional[Dict] = None,
    ):
        self.channel_id = channel_id
        self.name = name
        self.channel_type = channel_type
        self.agent = agent
        self.config = config or {}
        self.active = True
        self.created_at = datetime.now().isoformat()
        self.last_message = None
        self.message_count = 0

    def record_message(self, role: str, content: str):
        """Record a message on this channel."""
        self.last_message = {
            "role": role,
            "content": content[:200],
            "timestamp": datetime.now().isoformat(),
        }
        self.message_count += 1

    def to_dict(self) -> Dict:
        return {
            "channel_id": self.channel_id,
            "name": self.name,
            "channel_type": self.channel_type,
            "agent": self.agent,
            "active": self.active,
            "created_at": self.created_at,
            "last_message": self.last_message,
            "message_count": self.message_count,
        }


class Session:
    """Represents a conversation session across channels."""

    def __init__(self, session_id: str, agent: str, channel_id: str):
        self.session_id = session_id
        self.agent = agent
        self.channel_id = channel_id
        self.created_at = datetime.now().isoformat()
        self.last_active = self.created_at
        self.message_count = 0
        self.context: List[Dict] = []

    def add_message(self, role: str, content: str):
        """Add a message to the session."""
        self.context.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        self.last_active = datetime.now().isoformat()
        self.message_count += 1

    def get_context(self, max_messages: int = 20) -> List[Dict]:
        """Get recent context for this session."""
        return self.context[-max_messages:]

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "agent": self.agent,
            "channel_id": self.channel_id,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "message_count": self.message_count,
            "context_length": len(self.context),
        }


class GatewayLayer:
    """
    Unified channel routing for agent communication.
    - Manages channels (GUI, CLI, voice/text)
    - Tracks sessions across channels
    - Routes messages to the right agent
    - Logs all communication

    Multi-channel expansion (future):
    - Telegram, Discord, WhatsApp channels
    - Cross-platform session continuity
    - Channel-specific tool configuration
    """

    def __init__(self):
        self.channels: Dict[str, Channel] = {}
        self.sessions: Dict[str, Session] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self._register_default_channels()

    def _register_default_channels(self):
        """Register the default channels (Omnis GUI, Jarvis text, OpenCode CLI)."""
        self.register_channel("omnis_gui", "Omnis GUI", "gui", "omnis")
        self.register_channel("jarvis_text", "Jarvis Text", "text", "jarvis")
        self.register_channel("opencode_cli", "OpenCode CLI", "cli", "opencode")

    def register_channel(
        self, channel_id: str, name: str, channel_type: str, agent: str
    ) -> Channel:
        """Register a new communication channel."""
        channel = Channel(
            channel_id=channel_id,
            name=name,
            channel_type=channel_type,
            agent=agent,
        )
        self.channels[channel_id] = channel
        self._log_event("channel_registered", channel_id)
        return channel

    def create_session(self, session_id: str, agent: str, channel_id: str) -> Session:
        """Create a new conversation session."""
        session = Session(session_id, agent, channel_id)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def route_message(
        self,
        channel_id: str,
        session_id: str,
        role: str,
        content: str,
    ) -> Optional[str]:
        """
        Route a message through the gateway.
        Returns the target agent or None.
        Tracks session context and logs all communication.
        """
        channel = self.channels.get(channel_id)
        if not channel:
            self._log_event("routing_failed", f"Unknown channel: {channel_id}")
            return None

        channel.record_message(role, content)

        # Get or create session
        session = self.sessions.get(session_id)
        if not session:
            session = self.create_session(session_id, channel.agent, channel_id)

        session.add_message(role, content)

        # Check for handler
        handler = self.message_handlers.get(channel_id)
        if handler:
            try:
                handler(channel_id, session_id, role, content)
            except Exception as e:
                self._log_event("handler_error", f"{channel_id}: {str(e)}")

        self._log_event(
            "message_routed",
            f"{channel_id}/{session_id}: {role}",
        )

        return channel.agent

    def get_session_history(self, session_id: str, max_turns: int = 10) -> List[Dict]:
        """Get formatted session history for LLM context."""
        session = self.sessions.get(session_id)
        if not session:
            return []

        history = []
        for msg in session.context[-max_turns:]:
            history.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })
        return history

    def compact_session(self, session_id: str, max_messages: int = 20):
        """Compact old messages in a session to save memory."""
        session = self.sessions.get(session_id)
        if not session or len(session.context) <= max_messages:
            return

        # Keep first system message and last max_messages
        if session.context and session.context[0].get("role") == "system":
            system_msg = session.context[0]
            recent = session.context[-(max_messages-1):]
            session.context = [system_msg] + recent
        else:
            session.context = session.context[-max_messages:]

    def register_handler(self, channel_id: str, handler: Callable):
        """Register a message handler for a channel."""
        self.message_handlers[channel_id] = handler

    def get_channel_status(self, channel_id: str) -> Optional[Dict]:
        """Get status of a specific channel."""
        channel = self.channels.get(channel_id)
        return channel.to_dict() if channel else None

    def list_channels(self) -> List[Dict]:
        """List all registered channels."""
        return [c.to_dict() for c in self.channels.values()]

    def list_sessions(self, agent: Optional[str] = None) -> List[Dict]:
        """List all sessions, optionally filtered by agent."""
        sessions = []
        for s in self.sessions.values():
            if agent and s.agent != agent:
                continue
            sessions.append(s.to_dict())
        sessions.sort(key=lambda x: x["last_active"], reverse=True)
        return sessions

    def get_session_context(self, session_id: str, max_messages: int = 20) -> List[Dict]:
        """Get conversation context for a session."""
        session = self.sessions.get(session_id)
        if not session:
            return []
        return session.get_context(max_messages)

    def close_session(self, session_id: str) -> bool:
        """Close a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def _log_event(self, event: str, detail: str):
        """Log a gateway event."""
        log_entry = {
            "event": event,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            if CHANNEL_LOG_FILE.exists():
                log = json.loads(CHANNEL_LOG_FILE.read_text(encoding="utf-8"))
            else:
                log = []
            log.append(log_entry)
            CHANNEL_LOG_FILE.write_text(
                json.dumps(log[-500:], indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    def get_status(self) -> Dict[str, Any]:
        """Get gateway status."""
        return {
            "channels": len(self.channels),
            "active_channels": sum(1 for c in self.channels.values() if c.active),
            "sessions": len(self.sessions),
            "total_messages": sum(c.message_count for c in self.channels.values()),
            "handlers": list(self.message_handlers.keys()),
        }


def load_gateway_layer() -> GatewayLayer:
    """Factory function."""
    return GatewayLayer()


if __name__ == "__main__":
    import sys
    sys.path.insert(
        0, r"%USERPROFILE%\Desktop\AI projects\Projects\Omnis"
    )

    print("=== Gateway Layer - Phase 6 ===\n")

    gw = load_gateway_layer()

    # List default channels
    print("--- Default Channels ---")
    for c in gw.list_channels():
        print(f"  {c['name']} ({c['channel_type']}): agent={c['agent']}")

    # Route messages
    print("\n--- Routing Messages ---")
    gw.route_message("omnis_gui", "session_001", "user", "What models are running?")
    gw.route_message("omnis_gui", "session_001", "assistant", "SmolLM3-3B and Qwen3-1.7B via llama.cpp")

    gw.route_message("opencode_cli", "session_002", "user", "Check the unified layer files")
    gw.route_message("opencode_cli", "session_002", "assistant", "Found 12 files in unified_layer/")

    gw.route_message("jarvis_text", "session_003", "user", "Tell me about the vault")
    gw.route_message("jarvis_text", "session_003", "assistant", "114 notes, 251 connections, 8 MOCs")

    # List sessions
    print("\n--- Active Sessions ---")
    for s in gw.list_sessions():
        print(f"  {s['session_id']} ({s['agent']}): {s['message_count']} msgs")

    # Get context
    print("\n--- Session Context ---")
    ctx = gw.get_session_context("session_001")
    for msg in ctx:
        print(f"  {msg['role']}: {msg['content'][:60]}")

    print("\n--- Status ---")
    status = gw.get_status()
    print(json.dumps(status, indent=2))

    print("\nPhase 6 gateway layer test complete.")
