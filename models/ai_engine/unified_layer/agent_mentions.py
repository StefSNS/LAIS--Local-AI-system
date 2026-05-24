"""
Agent Mentions System - @AgentName syntax for invoking subagents.
Based on Codebuff's @AgentName feature.
"""

import re
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from unified_layer.agent_framework import get_agent_registry, get_agent_executor, AgentRegistry
from unified_layer.multi_agent_coordinator import get_multi_agent_coordinator


@dataclass
class AgentMention:
    """An @mention of an agent in text."""
    agent_id: str
    display_name: str
    prompt: str
    start_pos: int
    end_pos: int


class AgentMentionParser:
    """
    Parses @AgentName mentions from text.
    Supports: @AgentName prompt for agent
    """

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.pattern = re.compile(r'@(\w+)(?:\s+(.+))?$', re.MULTILINE)

    def parse(self, text: str) -> List[AgentMention]:
        """Parse all @mentions from text."""
        mentions = []
        lines = text.split('\n')

        for line in lines:
            if line.strip().startswith('@'):
                match = re.match(r'@(\w+)(?:\s+(.*))?', line.strip())
                if match:
                    agent_id = match.group(1)
                    prompt = match.group(2) or ""

                    if self.registry.get(agent_id):
                        mentions.append(AgentMention(
                            agent_id=agent_id,
                            display_name=self.registry.get(agent_id).display_name,
                            prompt=prompt,
                            start_pos=text.find(line),
                            end_pos=text.find(line) + len(line),
                        ))

        return mentions

    def extract_without_processing(self, text: str) -> Tuple[str, List[AgentMention]]:
        """Extract mentions but leave placeholder in text."""
        mentions = self.parse(text)
        processed_text = text

        for mention in reversed(mentions):
            placeholder = f"[AGENT: {mention.agent_id}]"
            processed_text = processed_text[:mention.start_pos] + placeholder + processed_text[mention.end_pos:]

        return processed_text, mentions


class AgentMentionExecutor:
    """
    Executes @AgentName mentions.
    Handles invoking subagents from user prompts.
    """

    def __init__(self, registry: AgentRegistry, executor, coordinator):
        self.registry = registry
        self.executor = executor
        self.coordinator = coordinator

    async def execute_mentions(
        self,
        mentions: List[AgentMention],
        main_prompt: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Execute all agent mentions and return results."""
        if not mentions:
            return {"success": True, "main_prompt": main_prompt, "agent_results": []}

        context = context or {}
        results = []

        for mention in mentions:
            agent = self.registry.get(mention.agent_id)
            if not agent:
                results.append({
                    "agent_id": mention.agent_id,
                    "success": False,
                    "error": f"Unknown agent: {mention.agent_id}",
                })
                continue

            prompt = mention.prompt or main_prompt
            result = await self.executor.execute(
                mention.agent_id,
                prompt,
                context,
            )
            results.append({
                "agent_id": mention.agent_id,
                "display_name": agent.display_name,
                "prompt": prompt,
                "result": result,
            })

        return {
            "success": True,
            "main_prompt": main_prompt,
            "mentions_found": len(mentions),
            "agent_results": results,
        }

    async def process_prompt_with_mentions(
        self,
        text: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Process a prompt, handling @mentions."""
        registry = get_agent_registry()
        parser = AgentMentionParser(registry)

        processed_text, mentions = parser.extract_without_processing(text)

        if not mentions:
            return {
                "success": True,
                "processed_text": text,
                "has_mentions": False,
            }

        result = await self.execute_mentions(mentions, text, context)

        return {
            "success": True,
            "processed_text": processed_text,
            "has_mentions": True,
            "mentions": [m.agent_id for m in mentions],
            "agent_results": result.get("agent_results", []),
        }


class BuiltInCommands:
    """
    Built-in slash commands similar to Codebuff's CLI commands.
    /new, /history, /init, /theme:toggle, /help
    """

    COMMANDS = {
        "help": {
            "description": "Show keyboard shortcuts and tips",
            "syntax": "/help",
        },
        "new": {
            "description": "Start a new conversation",
            "syntax": "/new",
        },
        "history": {
            "description": "Browse past conversations",
            "syntax": "/history",
        },
        "init": {
            "description": "Create starter knowledge.md",
            "syntax": "/init",
        },
        "theme:toggle": {
            "description": "Toggle light/dark mode",
            "syntax": "/theme:toggle",
        },
        "logout": {
            "description": "Sign out",
            "syntax": "/logout",
        },
        "exit": {
            "description": "Quit",
            "syntax": "/exit",
        },
        "feedback": {
            "description": "Share feedback",
            "syntax": "/feedback",
        },
    }

    @staticmethod
    def parse(text: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Parse commands from text."""
        lines = text.split('\n')
        commands = []

        for line in lines:
            line = line.strip()
            if line.startswith('/'):
                parts = line.split(None, 1)
                cmd = parts[0][1:]
                args = parts[1] if len(parts) > 1 else ""

                if cmd in BuiltInCommands.COMMANDS:
                    commands.append({
                        "command": cmd,
                        "args": args,
                        "spec": BuiltInCommands.COMMANDS[cmd],
                    })

        if not commands:
            return None, {}

        return commands[0]["command"] if commands else None, {"commands": commands}

    @staticmethod
    def get_help() -> str:
        """Get help text for all commands."""
        lines = ["Available Commands:"]
        for cmd, spec in BuiltInCommands.COMMANDS.items():
            lines.append(f"  {spec['syntax']} - {spec['description']}")
        return "\n".join(lines)


_mention_parser_instance: Optional[AgentMentionParser] = None
_mention_executor_instance: Optional[AgentMentionExecutor] = None


def get_mention_parser() -> AgentMentionParser:
    """Get or create the mention parser."""
    global _mention_parser_instance
    if _mention_parser_instance is None:
        registry = get_agent_registry()
        _mention_parser_instance = AgentMentionParser(registry)
    return _mention_parser_instance


def get_mention_executor() -> AgentMentionExecutor:
    """Get or create the mention executor."""
    global _mention_executor_instance
    if _mention_executor_instance is None:
        registry = get_agent_registry()
        executor = get_agent_executor()
        coordinator = get_multi_agent_coordinator()
        _mention_executor_instance = AgentMentionExecutor(registry, executor, coordinator)
    return _mention_executor_instance


if __name__ == "__main__":
    import json

    parser = get_mention_parser()
    executor = get_mention_executor()

    print("=== Agent Mentions System ===")

    test_text = """\
Fix the authentication bug
@debugger trace the login flow
@code_reviewer check for security issues
"""

    print("\n--- Parse Mentions ---")
    mentions = parser.parse(test_text)
    for m in mentions:
        print(f"  @{m.agent_id} -> {m.prompt[:30] if m.prompt else '(main prompt)'}")

    print("\n--- Extract Without Processing ---")
    processed, mentions = parser.extract_without_processing(test_text)
    print(f"Processed text:\n{processed}")

    print("\n--- Built-in Commands ---")
    command_text = """/new
/help
/theme:toggle debug mode
"""
    cmd, parsed = BuiltInCommands.parse(command_text)
    print(f"Parsed commands: {parsed}")

    print("\n--- Help ---")
    print(BuiltInCommands.get_help())

    print("\n--- Process Prompt ---")
    async def test():
        result = await executor.process_prompt_with_mentions(test_text, {"project": "test"})
        print(json.dumps(result, indent=2, default=str))

    asyncio.run(test())