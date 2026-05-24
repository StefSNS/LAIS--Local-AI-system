# JARVIS Voice AI (Mark XXXIX)

## Capabilities

- **Voice I/O** — Real-time via Gemini Live API
- **Screen Vision** — Capture and analyze screen contents
- **Webcam Capture** — Real-time video analysis
- **Desktop Control** — Mouse movement, clicks, keyboard input
- **Application Launch** — Open/close/manage Windows applications
- **Web Search** — Google + DuckDuckGo integration
- **Persistent Memory** — Remembers across sessions
- **Messaging** — WhatsApp and Telegram integration
- **Reminders** — Windows Task Scheduler automation
- **Game Management** — Steam, Epic Games launcher
- **YouTube** — Search, transcript, playback control
- **Flight Search** — Real-time flight data

## 9-Agent Security Grid

| Agent | Purpose |
|-------|---------|
| network_shield | Network traffic monitoring |
| code_sentry | Code execution validation |
| file_watchdog | File system change detection |
| input_sanitizer | Input validation and sanitization |
| auth_gate | Authentication and access control |
| anomaly_detector | Behavioral anomaly detection |
| crypto_guard | Encryption/decryption operations |
| audit_logger | Comprehensive audit trail |
| decoy_engine | Deception-based threat detection |

## Running

```bash
python models/Mark-XXXIX/main.py
```

## Configuration

Edit `models/Mark-XXXIX/config/api_keys.json`:

```json
{
  "gemini_api_key": "your-gemini-api-key-here",
  "telegram_token": "optional",
  "openweather_api_key": "optional"
}
```

## Voice Commands

- "Hey JARVIS" — Wake word
- "What's on my screen?" — Screen analysis
- "Open Chrome" — Launch application
- "Search for..." — Web search
- "Set a reminder for..." — Schedule reminder
- "Send a message to..." — WhatsApp/Telegram
- "What did I do yesterday?" — Memory recall

## Security

JARVIS runs with a 9-agent security grid that validates every operation. All voice commands pass through input sanitization. Screen captures are processed locally. API keys are stored encrypted at rest.
