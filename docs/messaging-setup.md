# LAIS Messaging Gateway Setup

Connect LAIS to Telegram, Discord, and WhatsApp.

## Quick Start

```bash
# Create the messaging config
python -m unified_layer.messaging_gateway init

# Edit config/messaging.json with your bot tokens
# Set "enabled": true for each platform

# Start all bridges
python -c "
from unified_layer.messaging_gateway import get_gateway
gw = get_gateway()
gw.start_in_thread()
"
```

## Telegram Setup

1. Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
2. Copy the bot token
3. Add to `config/messaging.json`:
```json
{
  "telegram": {
    "enabled": true,
    "token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
  }
}
```

**Required:** `pip install python-telegram-bot`

## Discord Setup

1. Create a bot at https://discord.com/developers/applications
2. Enable Message Content Intent in Bot settings
3. Copy the bot token
4. Add to `config/messaging.json`:
```json
{
  "discord": {
    "enabled": true,
    "token": "YOUR_DISCORD_BOT_TOKEN"
  }
}
```

**Required:** `pip install discord.py`

## WhatsApp Setup

WhatsApp integration requires a webhook endpoint. Options:

- **Twilio WhatsApp API** — Production-ready, paid
- **whatsapp-web.js** — Self-hosted, free, requires Node.js
- **Baileys** — Lightweight JS library

Configure the webhook URL in `config/messaging.json`.

## Architecture

```
Telegram ──┐
Discord  ──┼──→ MessagingGateway → Unified Layer → LAIS Agent
WhatsApp ──┘         │
                     ↓
              Response → Platform
```

Messages from any platform are normalized, routed to the correct LAIS agent via the CoComm protocol layer, and responses are sent back to the originating platform.
