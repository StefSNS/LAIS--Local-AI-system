"""
LAIS Messaging Gateway — Multi-platform messaging bridge.

Connects LAIS agents to external messaging platforms:
Telegram, Discord, and WhatsApp.

Architecture:
    Gateway receives messages from any platform → normalizes → routes to LAIS agents
    LAIS agents respond → Gateway formats → sends back to platform

Usage:
    from unified_layer.messaging_gateway import get_gateway

    gw = get_gateway()
    gw.start()  # Starts all configured bridges
"""

import asyncio
import json
import logging
import os
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger("lais.messaging")

LAIS_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_DIR = LAIS_ROOT / "config"
CONFIG_FILE = CONFIG_DIR / "messaging.json"


@dataclass
class Message:
    """Normalized message from any platform."""
    platform: str        # "telegram", "discord", "whatsapp"
    chat_id: str         # Platform-specific chat/channel identifier
    sender: str          # Sender display name
    text: str            # Message text
    message_id: str      # Platform-specific message ID
    timestamp: datetime = field(default_factory=datetime.now)
    attachments: list = field(default_factory=list)


class MessageBridge(ABC):
    """Abstract base for a platform messaging bridge."""

    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("enabled", False)
        self._handlers: list[Callable] = []
        self._running = False

    @abstractmethod
    async def start(self):
        """Start listening for messages on this platform."""

    @abstractmethod
    async def stop(self):
        """Stop the bridge."""

    @abstractmethod
    async def send(self, chat_id: str, text: str) -> bool:
        """Send a message to a chat."""

    def on_message(self, handler: Callable):
        """Register a handler for incoming messages."""
        self._handlers.append(handler)

    async def _dispatch(self, msg: Message):
        """Dispatch incoming message to all handlers."""
        for handler in self._handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(msg)
                else:
                    handler(msg)
            except Exception as e:
                logger.error(f"Handler error: {e}")


class TelegramBridge(MessageBridge):
    """Telegram bot bridge using python-telegram-bot."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.token = config.get("token", "")
        self._application = None

    async def start(self):
        if not self.token:
            logger.warning("Telegram: no token configured, skipping")
            return
        try:
            from telegram.ext import Application, MessageHandler, filters
            self._application = Application.builder().token(self.token).build()
            self._application.add_handler(MessageHandler(filters.TEXT, self._handle_update))
            await self._application.initialize()
            await self._application.start()
            await self._application.updater.start_polling()
            self._running = True
            logger.info("Telegram bridge started")
        except ImportError:
            logger.warning("Telegram: python-telegram-bot not installed. Install: pip install python-telegram-bot")
        except Exception as e:
            logger.error(f"Telegram: failed to start: {e}")

    async def stop(self):
        if self._application:
            await self._application.stop()
        self._running = False

    async def send(self, chat_id: str, text: str) -> bool:
        try:
            from telegram import Bot
            bot = Bot(self.token)
            await bot.send_message(chat_id=chat_id, text=text)
            return True
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False

    async def _handle_update(self, update, context):
        if not update.message or not update.message.text:
            return
        msg = Message(
            platform="telegram",
            chat_id=str(update.message.chat_id),
            sender=update.message.from_user.full_name or "Unknown",
            text=update.message.text,
            message_id=str(update.message.message_id),
        )
        await self._dispatch(msg)


class DiscordBridge(MessageBridge):
    """Discord bot bridge using discord.py."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.token = config.get("token", "")

    async def start(self):
        if not self.token:
            logger.warning("Discord: no token configured, skipping")
            return
        try:
            import discord
            intents = discord.Intents.default()
            intents.message_content = True

            class DiscordBot(discord.Client):
                def __init__(self, bridge):
                    super().__init__(intents=intents)
                    self.bridge = bridge

                async def on_ready(self):
                    logger.info(f"Discord bridge started as {self.user}")

                async def on_message(self, message):
                    if message.author == self.user:
                        return
                    msg = Message(
                        platform="discord",
                        chat_id=str(message.channel.id),
                        sender=message.author.display_name,
                        text=message.content,
                        message_id=str(message.id),
                    )
                    await self.bridge._dispatch(msg)

            self._client = DiscordBot(self)
            self._running = True
            asyncio.create_task(self._client.start(self.token))
            logger.info("Discord bridge started")
        except ImportError:
            logger.warning("Discord: discord.py not installed. Install: pip install discord.py")
        except Exception as e:
            logger.error(f"Discord: failed to start: {e}")

    async def stop(self):
        if self._client:
            await self._client.close()
        self._running = False

    async def send(self, chat_id: str, text: str) -> bool:
        try:
            import discord
            channel = self._client.get_channel(int(chat_id))
            if channel:
                await channel.send(text)
                return True
            return False
        except Exception as e:
            logger.error(f"Discord send error: {e}")
            return False


class WhatsAppBridge(MessageBridge):
    """WhatsApp bridge using whatsapp-web.js via HTTP."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.webhook_url = config.get("webhook_url", "")

    async def start(self):
        if not self.webhook_url:
            logger.warning("WhatsApp: no webhook configured, skipping")
            return
        self._running = True
        logger.info("WhatsApp bridge configured (webhook-based)")
        logger.info("Use whatsapp-web.js or a service like Twilio for production")

    async def stop(self):
        self._running = False

    async def send(self, chat_id: str, text: str) -> bool:
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json={
                    "chat_id": chat_id,
                    "text": text,
                }) as resp:
                    return resp.status == 200
        except ImportError:
            logger.warning("WhatsApp: aiohttp not installed")
        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
        return False


class MessagingGateway:
    """Central gateway that manages all platform bridges."""

    def __init__(self, config_path: str | Path | None = None):
        self.config_path = Path(config_path) if config_path else CONFIG_FILE
        self.config = self._load_config()
        self.bridges: dict[str, MessageBridge] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._loop = None

    def _load_config(self) -> dict:
        default_config = {
            "telegram": {"enabled": False, "token": ""},
            "discord": {"enabled": False, "token": ""},
            "whatsapp": {"enabled": False, "webhook_url": ""},
            "routing": {
                "default_agent": "ai_engine",
                "agent_map": {
                    "jarvis": ["telegram"],
                    "ai_engine": ["discord", "whatsapp"],
                    "opencode": [],
                }
            }
        }
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    loaded = json.load(f)
                    for key in default_config:
                        if key not in loaded:
                            loaded[key] = default_config[key]
                    return loaded
            except Exception as e:
                logger.warning(f"Failed to load messaging config: {e}")
        return default_config

    def save_config(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def init_bridges(self):
        """Initialize all configured bridges."""
        bridge_map = {
            "telegram": TelegramBridge,
            "discord": DiscordBridge,
            "whatsapp": WhatsAppBridge,
        }
        for platform, bridge_cls in bridge_map.items():
            platform_config = self.config.get(platform, {})
            if platform_config.get("enabled", False):
                bridge = bridge_cls(platform_config)
                bridge.on_message(self._on_message)
                self.bridges[platform] = bridge
                logger.info(f"Initialized {platform} bridge")

    async def start(self):
        """Start all bridges and the message processor."""
        self.init_bridges()
        self._running = True
        self._loop = asyncio.get_event_loop()

        tasks = []
        for name, bridge in self.bridges.items():
            logger.info(f"Starting {name} bridge...")
            tasks.append(asyncio.create_task(bridge.start()))

        tasks.append(asyncio.create_task(self._process_queue()))

        if tasks:
            await asyncio.gather(*tasks)

    async def stop(self):
        """Stop all bridges."""
        self._running = False
        for name, bridge in self.bridges.items():
            await bridge.stop()
        logger.info("All bridges stopped")

    def start_in_thread(self):
        """Start the gateway in a background thread (for non-async contexts)."""

        def _run():
            asyncio.run(self.start())

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread

    async def send_message(self, platform: str, chat_id: str, text: str) -> bool:
        """Send a message via a specific platform."""
        bridge = self.bridges.get(platform)
        if not bridge:
            logger.warning(f"No bridge for platform: {platform}")
            return False
        return await bridge.send(chat_id, text)

    async def broadcast(self, text: str, platforms: list[str] | None = None):
        """Broadcast a message to all or specified platforms."""
        targets = platforms or list(self.bridges.keys())
        results = {}
        for platform in targets:
            bridge = self.bridges.get(platform)
            if bridge:
                for chat_id in self._get_broadcast_targets(platform):
                    results[f"{platform}:{chat_id}"] = await bridge.send(chat_id, text)
        return results

    def _get_broadcast_targets(self, platform: str) -> list[str]:
        """Get chat IDs to broadcast to for a platform."""
        return self.config.get("broadcast_targets", {}).get(platform, [])

    async def _on_message(self, msg: Message):
        """Handle incoming message from any bridge."""
        await self._message_queue.put(msg)

    async def _process_queue(self):
        """Process incoming messages from the queue."""
        while self._running:
            try:
                msg = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
                await self._route_message(msg)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Queue processing error: {e}")

    async def _route_message(self, msg: Message):
        """Route a message to the appropriate LAIS agent."""
        routing = self.config.get("routing", {})
        agent_map = routing.get("agent_map", {})

        target_agent = routing.get("default_agent", "ai_engine")
        for agent, platforms in agent_map.items():
            if msg.platform in platforms:
                target_agent = agent
                break

        logger.info(f"Routing {msg.platform} message from {msg.sender} to {target_agent}")

        try:
            from unified_layer.protocol_layer import load_protocol_layer
            proto = load_protocol_layer()
            if proto:
                response = proto.send_a2a_message(
                    from_agent=f"messaging:{msg.platform}",
                    to_agent=target_agent,
                    message_type="query",
                    payload={
                        "text": msg.text,
                        "sender": msg.sender,
                        "chat_id": msg.chat_id,
                        "platform": msg.platform,
                    }
                )
                if response:
                    await self.send_message(msg.platform, msg.chat_id, str(response))
        except Exception as e:
            logger.error(f"Message routing error: {e}")
            await self.send_message(msg.platform, msg.chat_id, f"Error processing message: {e}")


# Module-level singleton
_gateway: MessagingGateway | None = None


def get_gateway(config_path: str | Path | None = None) -> MessagingGateway:
    """Get or create the messaging gateway singleton."""
    global _gateway
    if _gateway is None:
        _gateway = MessagingGateway(config_path)
    return _gateway


def create_default_config():
    """Create a default messaging config file for user to edit."""
    gateway = get_gateway()
    gateway.save_config()
    print(f"[LAIS] Messaging config created at {CONFIG_FILE}")
    print(f"[LAIS] Add your bot tokens and set enabled: true for each platform")
    return CONFIG_FILE


# CLI entry point
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "init":
        create_default_config()
    else:
        print("Usage: python messaging_gateway.py init")
        print("  init  - Create default messaging config file")
