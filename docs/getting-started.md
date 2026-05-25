# Getting Started with LAIS

## Prerequisites

- **Python 3.11 or higher** ([python.org](https://python.org))
- **Git** ([git-scm.com](https://git-scm.com))
- **Windows 10/11** (for full feature support) or **Linux/macOS** (for headless services)
- **Gemini API key** ([get one free](https://aistudio.google.com/apikey))

## Windows Installation (One-Liner)

Open PowerShell and run:

```powershell
powershell -c "irm https://raw.githubusercontent.com/StefSNS/LAIS--Local-AI-system/main/install.ps1 | iex"
```

The installer will:
1. Check prerequisites (Python 3.11+, Git)
2. Clone the repository to `$env:USERPROFILE\LAIS`
3. Install all Python dependencies
4. Set up token optimization pipeline
5. Create knowledge vault structure
6. Validate the build

## Linux/macOS Installation

```bash
bash <(curl -s https://raw.githubusercontent.com/StefSNS/LAIS--Local-AI-system/main/install.sh)
```

## Manual Installation

```bash
git clone --depth 1 https://github.com/StefSNS/LAIS--Local-AI-system.git
cd LAIS--Local-AI-system
python install.py
```

## Configure API Keys

Edit `models/Mark-XXXIX/config/api_keys.json`:

```json
{
  "gemini_api_key": "your-gemini-api-key-here"
}
```

## Running the Agents

### JARVIS Voice AI
```bash
python models/Mark-XXXIX/main.py
```
Voice commands, screen vision, webcam, desktop control.

### AI Engine GUI
```bash
python models/ai_engine/main.py
```
Desktop orchestrator with 40+ plugins.

### Headless REST API
```bash
```
Or directly:
```bash
```

## Next Steps

- Read the [Architecture Overview](architecture.md)
- Configure [Messaging Gateways](messaging.md) (Telegram/Discord)
- Learn about [Memory Architecture](memory.md)
- Explore [CoComm Protocol](cocomm.md)
