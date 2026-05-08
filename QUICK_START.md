# Quick Start Guide

> **5 minutes to your first conversation with MARK XXXV.**

---

## Step 1: Prerequisites

- [ ] **Windows 10 or 11**
- [ ] **Python 3.11 or 3.12** — [Download](https://www.python.org/downloads/)
- [ ] **Google Gemini API Key** — [Get one free](https://aistudio.google.com/apikey)
- [ ] **Microphone** (built-in or external)
- [ ] **Internet connection**

## Step 2: Install

### Option A: One-Click Install (Recommended)

Open **PowerShell as Administrator** and run:

```powershell
pip install localclaw
```

This automatically handles everything.

### Option B: Manual Install

```powershell
# Clone
git clone https://github.com/JARVIS-Systems/Mark-XXXV.git
cd Mark-XXXV

# Python dependencies
pip install -r requirements.txt

# Browser automation
playwright install chromium
```

## Step 3: Configure Your API Key

Create a file named `.env` in the project root with:

```ini
GEMINI_API_KEY=AIzaSy...
```

**Don't have a key?** Go to https://aistudio.google.com/apikey and click "Create API Key." It's free with usage quotas.

## Step 4: Launch

```powershell
python main.py
```

On first launch, you'll see:
1. A **UI prompt** for your API key (or it reads from `.env`)
2. The animated JARVIS interface appears
3. You'll hear: *"At your service, sir."*

## Step 5: Personalize

The assistant learns about you automatically. Tell it things like:

```text
"My name is Alex"
"I'm a software developer"
"I work on AI projects"
"My favorite color is blue"
```

It will remember these across sessions.

## Step 6: First Commands

Try these in order:

```text
1. "What can you do?"
2. "What's on my screen?"
3. "Open Notepad"
4. "Search for today's weather in London"
5. "Check my system health"
6. "Set a reminder for 10 minutes called 'stand up'"
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `No module named ...` | Run `pip install -r requirements.txt` |
| `API key not found` | Ensure `.env` file exists with `GEMINI_API_KEY=...` |
| `No audio` | Check microphone: Settings → Privacy → Microphone |
| `Playwright not found` | Run `playwright install chromium` |
| `Connection failed` | Check internet, VPN, or firewall blocking Google APIs |
| `UI not showing` | Ensure Tkinter is installed: `python -m tkinter` |

---

## Next Steps

- Read [USER_GUIDE.md](USER_GUIDE.md) for complete command reference
- Read [SECURITY.md](SECURITY.md) for security best practices
- Explore the `actions/` folder to see all available tools
