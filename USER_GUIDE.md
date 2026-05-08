# User Guide — MARK XXXV

> Complete reference for using the personal AI assistant.

---

## Interface

### UI Layout

The animated Tkinter interface shows:

- **Face display** — Animated circular face in the center
- **Status indicator** — Top of window shows current state:
  - `LISTENING` — Ready for voice input
  - `SPEAKING` — Assistant is responding
  - `THINKING` — Processing a tool call
  - `MUTED` — Microphone disabled
- **Log panel** — Bottom section shows conversation history
- **Text input** — Type commands instead of speaking (keyboard bar at bottom)
- **F4 key** — Toggle microphone mute at any time

### States

| State | What It Means | What To Do |
|---|---|---|
| LISTENING | Mic is active, waiting for your voice | Speak naturally |
| SPEAKING | JARVIS is responding | Wait for response to complete |
| THINKING | Processing a tool/command | Momentary — no action needed |
| MUTED | Mic disabled | Press F4 to unmute |

---

## Voice Commands

### Computer Control

| Command | Action |
|---|---|
| "Open Chrome" | Launches Chrome browser |
| "Open Spotify" | Launches Spotify |
| "Open calculator" | Opens Windows Calculator |
| "Type hello world" | Types text at current cursor |
| "Press enter" | Sends Enter key |
| "Click at x:500 y:300" | Clicks at screen coordinates |
| "Scroll down" | Scrolls page down |
| "Take a screenshot" | Captures and saves screenshot |
| "Lock my computer" | Locks Windows |
| "Restart the PC" | Restarts computer |
| "Volume 50%" | Sets volume to 50% |
| "Brightness 75%" | Sets display brightness |
| "Mute" | Mutes all audio |
| "Turn on dark mode" | Toggles Windows dark mode |
| "Close this window" | Closes active window |
| "Minimize all windows" | Shows desktop |

### Web & Search

| Command | Action |
|---|---|
| "Search for quantum computing" | Web search with results |
| "Search and compare iPhone vs Samsung" | Comparison mode |
| "Go to google.com" | Opens URL in browser |
| "What's the weather in Tokyo?" | Current weather |
| "Find flights from London to Paris on Friday" | Google Flights search |

### File Management

| Command | Action |
|---|---|
| "List files on my desktop" | Shows desktop files |
| "Create a file called notes.txt" | Creates new file |
| "Write hello world to notes.txt" | Writes content to file |
| "Show me my downloads folder" | Lists Downloads |
| "Find all PDF files" | Searches for PDFs |
| "Check disk usage" | Shows drive space |
| "Delete old_file.txt" | Sends to recycle bin |

### Browser Automation

| Command | Action |
|---|---|
| "Open Amazon and search for laptop" | Navigate + search |
| "Click the search button" | Clicks element by text |
| "Fill in the email field" | Types into form field |
| "Scroll to bottom of page" | Scrolls down |
| "Go back" | Browser back button |

### Messaging & Reminders

| Command | Action |
|---|---|
| "Send a message to John on WhatsApp saying I'll be late" | WhatsApp message |
| "Send a Telegram to Anna saying happy birthday" | Telegram message |
| "Remind me to call mom at 3 PM" | Windows task scheduler reminder |
| "Set a reminder for tomorrow at 9 AM called 'meeting'" | Scheduled reminder |

### YouTube & Media

| Command | Action |
|---|---|
| "Play the song Despacito on YouTube" | Opens and plays video |
| "Summarize this YouTube video" | Gets video transcript + summary |
| "What's trending on YouTube in the US?" | Trending videos |
| "Get info on this video" | Video details |

### Code & Development

| Command | Action |
|---|---|
| "Write a Python script to sort a list" | Generates code |
| "Explain this code: print('hello')" | Code explanation |
| "Run the script test.py" | Executes file |
| "Build a todo app with Flask" | Creates multi-file project |

### Memory

| Command | Action |
|---|---|
| "My name is Alex" | Saves name to memory |
| "I work at Google" | Saves job info |
| "My sister's name is Sarah" | Saves relationship |
| "Remember I like Italian food" | Saves preference |
| "What do you know about me?" | Recalls all memories |

### Gaming

| Command | Action |
|---|---|
| "Install Cyberpunk 2077 from Steam" | Installs via Steam |
| "Update all my Steam games" | Updates all Steam games |
| "List my installed games" | Shows installed games |
| "Schedule game updates at 3 AM" | Schedules nightly updates |

### System & Security

| Command | Action |
|---|---|
| "Run a system diagnostic" | Full system health check |
| "Check my CPU usage" | Processor status |
| "How much RAM do I have?" | Memory info |
| "Check my internet speed" | Network diagnostics |
| "Deploy security grid — medium threat" | Activates defense agents |
| "Security status" | Shows active defenses |
| "Disarm security" | Deactivates defense grid |

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `F4` | Toggle microphone mute |
| `Enter` (in text bar) | Send typed command |
| `Esc` (in text bar) | Clear text input |

---

## Configuration

### API Key

The assistant needs a Google Gemini API key. Set it in `.env`:

```ini
GEMINI_API_KEY=your_key_here
```

On first launch, the UI will prompt you to enter it if not found.

### System Prompt

Edit `core/prompt.txt` to customize the assistant's personality, rules, and behavior. This is the system instruction sent to Gemini with every request.

### Memory

Long-term memory is stored in `memory/long_term.json`. You can:
- View it directly in any text editor
- Delete it to reset all memories
- Edit entries manually

---

## Advanced Usage

### Running Local Models

GGUF models are included in the `models/` directory for local inference via llama.cpp:
- `Qwen3.5-4B-Q4_K_M.gguf`
- `Qwen3.5-2B-Q4_K_M.gguf`
- `rwkv7-2.9B-world-Q4_K_M.gguf`
- `HuggingFaceTB_SmolLM3-3B-Q4_K_M.gguf`

Use `llama-cli.exe` from `llama-bin/` to run them:

```powershell
./llama-bin/llama-cli.exe -m models/Qwen3.5-4B-Q4_K_M.gguf -p "Hello"
```

### Multi-Step Tasks

Use the `agent_task` tool for complex multi-step goals:

```text
"Research the history of AI, save it to a file on my desktop, and open it"
```

The agent will: plan → search → create file → open file, with error recovery.

### Autonomous Project Building

```text
"Build a personal budget tracker web app with Flask and SQLite"
```

The `dev_agent` will: plan files → write code → install deps → open in VSCode → run and fix errors.

---

## Security

⚠️ **IMPORTANT**: This assistant has extensive system access.

- Review [SECURITY.md](SECURITY.md) before deployment
- The `.env` file contains your API key — **never share or commit it**
- Memory data is stored unencrypted in `memory/long_term.json`
- Use a limited Windows user account for untrusted environments
- The security grid can be deployed on-demand for threat response

---

## Tips & Best Practices

1. **Be specific** — "Open Chrome and go to gmail.com" works better than "Open the browser"
2. **Use natural language** — The model understands conversational commands
3. **Verify critical actions** — Review file deletes and command executions in the log panel
4. **Use F4** — Mute the mic during side conversations to prevent accidental triggers
5. **Check logs** — The UI log panel shows all tool calls and their results
6. **Memory is automatic** — No need to say "remember this" — the system extracts facts passively
