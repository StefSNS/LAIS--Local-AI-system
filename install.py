"""
MARK XXXV — Complete System Installer
=======================================
Bootstraps the full unified AI ecosystem:
  • MARK XXXV voice assistant (JARVIS)
  • Local AI engine (GGUF + Gemini)
  • OpenCode CLI agent
  • Obsidian "Shared Brain" vault
  • All skills, plugins, and integrations

Usage:
    python install.py

Or with pip (once published):
    pip install localclaw
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path


# ─── Configuration ────────────────────────────────────────────────────────────

REPOS = {
    "mark-xxxv": {
        "url": "https://github.com/JARVIS-Systems/Mark-XXXV.git",
        "dir": "Mark-XXXV",
        "description": "Voice-driven personal AI assistant",
    },
    "opencode": {
        "url": "https://github.com/anomalyco/opencode.git",
        "dir": "opencode",
        "description": "CLI coding agent (local skills-based)",
    },
}

OBSIDIAN_URL = "https://github.com/obsidianmd/obsidian-releases/releases/latest/download/Obsidian.1.8.9.exe"
SELF_DIR = Path(__file__).resolve().parent


# ─── Utilities ────────────────────────────────────────────────────────────────

def step(msg):
    print(f"\n  {'='*60}")
    print(f"  >>> {msg}")
    print(f"  {'='*60}")

def ok(msg):
    print(f"  [OK] {msg}")

def warn(msg):
    print(f"  [!] {msg}")

def fail(msg):
    print(f"  [FAIL] {msg}")
    return False

def run(cmd, cwd=None, timeout=120):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return False, "", str(e)


# ─── Phase 1: System Check ───────────────────────────────────────────────────

def phase_system_check():
    step("Phase 1/9: System Check")

    if sys.version_info < (3, 11):
        return fail(f"Python 3.11+ required (got {sys.version_info.major}.{sys.version_info.minor})")
    ok(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    git_ok, _, _ = run(["git", "--version"])
    if not git_ok:
        return fail("Git not found. Install from https://git-scm.com")
    ok("Git found")

    pip_ok, _, _ = run([sys.executable, "-m", "pip", "--version"])
    if not pip_ok:
        return fail("pip not found")
    ok("pip found")

    return True


# ─── Phase 2: Clone Repositories ─────────────────────────────────────────────

def phase_clone_repos(desktop):
    step("Phase 2/9: Downloading Components")

    results = {}
    for key, repo in REPOS.items():
        target = SELF_DIR / "models" / repo["dir"]
        if target.exists():
            ok(f"{repo['dir']} already exists, skipping")
            results[key] = target
            continue

        print(f"  Cloning {repo['description']}...")
        ok_zip, _, _ = run(["git", "clone", "--depth", "1", repo["url"], str(target)])
        if not ok_zip:
            warn(f"Git clone failed, trying ZIP fallback...")
            zip_path = SELF_DIR / f"{repo['dir']}.zip"
            zip_url = repo["url"].replace(".git", "/archive/refs/heads/main.zip")
            try:
                urllib.request.urlretrieve(zip_url, zip_path)
                with zipfile.ZipFile(zip_path) as zf:
                    zf.extractall(SELF_DIR / "models")
                zip_path.unlink()
                extracted = SELF_DIR / "models" / f"{repo['dir']}-main"
                if extracted.exists():
                    extracted.rename(target)
                ok(f"{repo['dir']} downloaded via ZIP")
            except Exception as e:
                return fail(f"Could not download {repo['dir']}: {e}")

        if target.exists():
            results[key] = target
            ok(f"{repo['dir']} ready")
        else:
            results[key] = None

    return results


# ─── Phase 3: Build Clean AI Engine ──────────────────────────────────────────

def phase_build_ai_engine(desktop):
    step("Phase 3/9: Verifying Local AI Engine")

    engine_dir = SELF_DIR / "models" / "ai_engine"
    if not engine_dir.exists() or not (engine_dir / "main.py").exists():
        return fail("AI Engine not found in models/ai_engine/ — re-download the package")

    ok(f"AI Engine found: {engine_dir}")
    return engine_dir


def phase_validate_ai_engine(engine_dir):
    """Run syntax validation on all Python files."""
    step("Phase 3b/9: Validating AI Engine Build")

    errors = []
    for py_file in sorted(engine_dir.rglob("*.py")):
        rel = py_file.relative_to(engine_dir)
        try:
            compile(py_file.read_text(encoding="utf-8", errors="ignore"), str(py_file), "exec")
        except SyntaxError as e:
            errors.append(f"{rel}: {e}")
            warn(f"Syntax error: {rel}")

    if errors:
        warn(f"{len(errors)} files with syntax errors (likely non-critical)")
        for e in errors[:5]:
            print(f"    {e}")
    else:
        ok(f"All Python files pass syntax check ({len(list(engine_dir.rglob('*.py')))} files)")

    return len(errors) == 0


# ─── Phase 4: Install Dependencies ───────────────────────────────────────────

def phase_install_deps():
    step("Phase 4/9: Installing Dependencies")

    # Install Mark-XXXV deps
    req_file = SELF_DIR / "models" / "Mark-XXXV" / "requirements.txt"
    if req_file.exists():
        ok_install, out, err = run([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
        if not ok_install:
            warn(f"pip install had issues:\n{err[:300]}")
        else:
            ok("Python dependencies installed")

    # Install Playwright
    ok_play, _, _ = run([sys.executable, "-m", "playwright", "install", "chromium"])
    if ok_play:
        ok("Playwright Chromium installed")

    return True


# ─── Phase 5: Create Obsidian "Shared Brain" Vault ──────────────────────────

VAULT_STRUCTURE = {
    "000_INBOX": {},
    "001_PROJECTS": {
        "Active": {},
        "Archived": {},
        "Ideas": {},
    },
    "002_AREAS": {
        "Coding": {},
        "Learning": {},
        "Health": {},
        "Finance": {},
    },
    "003_RESOURCES": {
        "Tutorials": {},
        "Books": {},
        "Articles": {},
        "Tools": {},
    },
    "004_ARCHIVES": {},
    "005_KNOWLEDGE": {
        "Python": {},
        "JavaScript": {},
        "TypeScript": {},
        "Rust": {},
        "Go": {},
        "Shell": {},
        "SQL": {},
        "AI_ML": {},
        "System_Design": {},
    },
    "010_AGENTS": {
        "JARVIS": {},
        "OpenCode": {},
        "AI_Engine": {},
        "Skills": {},
    },
    "020_DASHBOARDS": {},
}

CODING_LANGUAGE_NOTES = {
    "Python.md": """# Python

## Quick Start
- **Use for**: AI/ML, automation, web backends, scripting
- **Package manager**: pip
- **Key libraries**: requests, fastapi, pandas, numpy, torch

## Common Patterns
```python
# Virtual environment
python -m venv .venv
.venv\\Scripts\\activate

# Install packages
pip install requests

# Basic script
def main():
    print("Hello, world!")

if __name__ == "__main__":
    main()
```

## Prompts for AI
- "Write a Python script to..."
- "Debug this Python error: ..."
- "Explain this Python code..."
""",
    "JavaScript.md": """# JavaScript

## Quick Start
- **Use for**: Web frontends, Node.js backends, browser automation
- **Package manager**: npm/yarn/pnpm
- **Key libraries**: react, express, axios, lodash

## Common Patterns
```javascript
// Initialize project
npm init -y
npm install express

// Basic server
const express = require('express');
const app = express();
app.listen(3000);
```

## Prompts for AI
- "Create a React component that..."
- "Debug this JavaScript: ..."
""",
    "TypeScript.md": """# TypeScript

## Quick Start
- **Use for**: Type-safe web development, large-scale apps
- **Package manager**: npm/yarn/pnpm
- **Key libraries**: react, nextjs, typescript, zod

## Common Patterns
```typescript
// Initialize
npx tsc --init
npm install typescript @types/node

// Basic types
interface User {
  id: string;
  name: string;
}
```
""",
    "Shell.md": """# Shell / PowerShell

## Quick Start
- **Use for**: Automation, file management, system administration
- **Shells**: PowerShell (Windows), Bash (Linux/Mac)

## Common Patterns
```powershell
# PowerShell
Get-ChildItem -Path "C:\\path"
Set-Content -Path "file.txt" -Value "content"
```

## Prompts for AI
- "Write a PowerShell script to..."
- "Create a bash command that..."
""",
    "SQL.md": """# SQL

## Quick Start
- **Use for**: Database queries, data analysis, reporting
- **Engines**: SQLite, PostgreSQL, MySQL, SQL Server

## Common Patterns
```sql
-- Query
SELECT * FROM users WHERE name = 'Alex';

-- Create table
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Prompts for AI
- "Write a query to find..."
- "Optimize this SQL: ..."
""",
}

def _create_vault_structure(vault_dir, structure, parent_path=""):
    for name, children in structure.items():
        dir_path = vault_dir / name
        dir_path.mkdir(parents=True, exist_ok=True)
        _create_vault_structure(vault_dir, children, name)


def phase_create_vault(desktop):
    step("Phase 5/9: Creating Obsidian 'Shared Brain' Vault")

    vault_dir = desktop / "Shared Brain"
    if vault_dir.exists():
        warn(f"Vault already exists at {vault_dir}")
        overwrite = input("  Overwrite? (y/N): ").strip().lower()
        if overwrite != "y":
            ok("Skipping vault creation")
            return vault_dir

    # Create structure
    _create_vault_structure(vault_dir, VAULT_STRUCTURE)
    ok("Vault folder structure created")

    # Create coding language notes
    lang_dir = vault_dir / "005_KNOWLEDGE"
    for filename, content in CODING_LANGUAGE_NOTES.items():
        (lang_dir / filename).write_text(content, encoding="utf-8")
    ok(f"Coding language notes added ({len(CODING_LANGUAGE_NOTES)} languages)")

    # Create .obsidian config
    obsidian_dir = vault_dir / ".obsidian"
    obsidian_dir.mkdir(exist_ok=True)

    (obsidian_dir / "app.json").write_text(json.dumps({
        "alwaysUpdateLinks": True,
        "attachmentFolderPath": "000_INBOX",
        "newFileLocation": "current",
        "useMarkdownLinks": True,
        "showLineNumber": True,
        "tabSize": 4,
    }, indent=2))

    (obsidian_dir / "appearance.json").write_text(json.dumps({
        "accentColor": "#7c3aed",
        "baseTheme": "obsidian",
        "cssTheme": "",
        "enabledCssSnippets": [],
        "interfaceFontFamily": "",
        "textFontFamily": "",
        "theme": "obsidian",
    }, indent=2))

    (obsidian_dir / "core-plugins.json").write_text(json.dumps({
        "file-explorer": True,
        "global-search": True,
        "switcher": True,
        "graph": True,
        "backlink": True,
        "outgoing-link": True,
        "tag-pane": True,
        "page-preview": True,
        "daily-notes": True,
        "templates": True,
        "note-composer": True,
        "command-palette": True,
        "slash-command": True,
        "editor-status": True,
        "starred": True,
        "markdown-importer": True,
        "word-count": True,
        "file-recovery": True,
    }, indent=2))

    (obsidian_dir / "community-plugins.json").write_text(json.dumps([
        "obsidian-git",
        "dataview",
        "templater-obsidian",
        "obsidian-kanban",
        "calendar",
        "obsidian-tasks-plugin",
    ], indent=2))

    ok(f"Vault created at {vault_dir} with {len(CODING_LANGUAGE_NOTES)} language notes")
    return vault_dir


# ─── Phase 6: Install Skills ─────────────────────────────────────────────────

def _gather_skills(vault_dir):
    """Collect skills from all system components into a central registry."""
    skills_registry = []
    skill_sources = []

    # From vault
    vault_skills = vault_dir / "010_AGENTS" / "Skills"
    vault_skills.mkdir(parents=True, exist_ok=True)
    skill_sources.append(("Vault", vault_skills))

    # From Mark-XXXV
    jarvis_agent = SELF_DIR / "models" / "Mark-XXXV" / "agent"
    if jarvis_agent.exists():
        for f in jarvis_agent.rglob("*.py"):
            skills_registry.append({
                "source": "JARVIS",
                "name": f.stem,
                "path": str(f.relative_to(SELF_DIR)),
                "type": "agent_module",
            })

    # From OpenCode skills (if cloned)
    opencode_skills = SELF_DIR / "models" / "opencode" / "skills"
    if opencode_skills.exists():
        for f in opencode_skills.rglob("*.md"):
            skills_registry.append({
                "source": "OpenCode",
                "name": f.stem,
                "path": str(f.relative_to(SELF_DIR)),
                "type": "skill",
            })

    # From AI Engine plugins
    ai_engine_plugins = SELF_DIR / "models" / "ai_engine" / "plugins"
    if ai_engine_plugins.exists():
        for f in ai_engine_plugins.rglob("*.py"):
            skills_registry.append({
                "source": "AI_Engine",
                "name": f.stem,
                "path": str(f.relative_to(SELF_DIR)),
                "type": "plugin",
            })

    # Registry file
    registry_path = vault_skills / "_REGISTRY.md"
    lines = ["# Skills Registry\n", f"*Generated: {time.strftime('%Y-%m-%d %H:%M')}*\n", ""]
    lines.append(f"| # | Source | Name | Type |")
    lines.append(f"|---|--------|------|------|")
    for i, s in enumerate(skills_registry, 1):
        lines.append(f"| {i} | {s['source']} | `{s['name']}` | {s['type']} |")
    registry_path.write_text("\n".join(lines), encoding="utf-8")

    return skills_registry


def phase_install_skills(vault_dir):
    step("Phase 6/9: Installing Skills & Plugins")

    skills = _gather_skills(vault_dir)
    ok(f"Skills registry created: {len(skills)} entries")

    # Create integration links
    jarvis_link = vault_dir / "010_AGENTS" / "JARVIS" / "_README.md"
    jarvis_link.write_text("""# JARVIS Agent

## Integration
- **Repo**: `models/Mark-XXXV/`
- **Entry**: `python main.py`
- **Status**: Voice-driven personal AI assistant

## Available Tools
See `main.py` TOOL_DECLARATIONS for the full list of 20+ function calls.

## Memory
Long-term memory stored in `models/Mark-XXXV/memory/long_term.json`
""", encoding="utf-8")

    opencode_link = vault_dir / "010_AGENTS" / "OpenCode" / "_README.md"
    opencode_link.write_text("""# OpenCode Agent

## Integration
- **Repo**: `models/opencode/`
- **Entry**: `opencode` CLI command
- **Status**: Local coding agent with skills

## Commands
```powershell
opencode    # Launch in current directory
```

## Skills
Skills directory: `models/opencode/skills/`
""", encoding="utf-8")

    ai_link = vault_dir / "010_AGENTS" / "AI_Engine" / "_README.md"
    ai_link.write_text("""# Local AI Engine

## Integration
- **Location**: `models/ai_engine/`
- **Status**: Local LLM inference + API orchestration

## Capabilities
- Gemini API integration
- Local GGUF model inference (Qwen, RWKV, SmolLM)
- Plugin system
- Unified memory layer
""", encoding="utf-8")

    ok("Agent integration docs created in vault")
    return skills


# ─── Phase 7: Unified Integration ───────────────────────────────────────────

def phase_unified_integration(vault_dir):
    step("Phase 7/9: Creating Unified System Integration")

    config_dir = SELF_DIR / "config"
    config_dir.mkdir(exist_ok=True)

    integration_config = {
        "version": "1.0.0",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agents": {
            "jarvis": {
                "path": str(SELF_DIR / "models" / "Mark-XXXV"),
                "entry": "main.py",
                "enabled": True,
            },
            "opencode": {
                "path": str(SELF_DIR / "models" / "opencode"),
                "entry": "opencode",
                "enabled": True,
            },
            "ai_engine": {
                "path": str(SELF_DIR / "models" / "ai_engine"),
                "entry": "main.py",
                "enabled": True,
            },
        },
        "vault": {
            "path": str(vault_dir),
            "name": "Shared Brain",
        },
    }

    (config_dir / "system.json").write_text(json.dumps(integration_config, indent=2))

    # Create launch scripts
    launch_dir = SELF_DIR / "launch"
    launch_dir.mkdir(exist_ok=True)

    # Launch all
    (launch_dir / "start_all.ps1").write_text(f"""# Start Unified AI System
Write-Host "Starting Unified AI System..." -ForegroundColor Cyan

# 1. AI Engine (background)
$aiPath = "{SELF_DIR / 'models' / 'ai_engine' / 'main.py'}"
if (Test-Path $aiPath) {{
    Write-Host "  [AI Engine] Starting..." -ForegroundColor Yellow
    Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "$aiPath"
}}

# 2. JARVIS
$jarvisPath = "{SELF_DIR / 'models' / 'Mark-XXXV' / 'main.py'}"
if (Test-Path $jarvisPath) {{
    Write-Host "  [JARVIS] Starting..." -ForegroundColor Yellow
    Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "$jarvisPath"
}}

# 3. Obsidian vault
$vaultPath = "{vault_dir}"
if (Test-Path $vaultPath) {{
    Write-Host "  [Vault] Opening..." -ForegroundColor Yellow
    Start-Process "obsidian://open?vault=$vaultPath"
}}

Write-Host "System started!" -ForegroundColor Green
""")

    (launch_dir / "open_opencode.ps1").write_text(f"""# Open OpenCode in the project directory
$projectDir = "{SELF_DIR}"
Set-Location -LiteralPath $projectDir
opencode
""")

    ok("Unified integration config created")
    ok(f"Launch scripts in: {launch_dir}")
    return True


# ─── Phase 8: Create User Guides ────────────────────────────────────────────

def phase_create_guides(desktop, vault_dir):
    step("Phase 8/9: Creating User Guides & Prompts")

    # Quick reference card for the vault
    quick_ref = vault_dir / "000_INBOX" / "_SYSTEM_QUICK_REFERENCE.md"
    quick_ref.write_text(f"""# Unified AI System — Quick Reference

## Your Agents

| Agent | How to Use | Location |
|-------|-----------|----------|
| **JARVIS** | Speak naturally (mic required) | `python models/Mark-XXXV/main.py` |
| **OpenCode** | `opencode` in terminal | `models/opencode/` |
| **AI Engine** | Python API + local inference | `models/ai_engine/` |

## First Prompts

### For JARVIS (speak these):
```
"What can you do?"
"Open Chrome and search for..."
"What's on my screen?"
"Remember that my name is Alex"
"Run a system diagnostic"
```

### For OpenCode (type these):
```
/help                          # See available commands
"Write a Python script to..."  # Natural language task
"Explain this code: ..."       # Code explanation
```

### For AI Engine (via Python):
```python
from ai_engine import ask
response = ask("What is the capital of France?")
print(response)
```

## Obsidian Vault Structure

```
Shared Brain/
├── 000_INBOX/          # Quick capture, new ideas
├── 001_PROJECTS/       # Active & archived projects
├── 002_AREAS/          # Coding, Learning, Health, Finance
├── 003_RESOURCES/      # Tutorials, Books, Articles, Tools
├── 004_ARCHIVES/       # Completed / reference
├── 005_KNOWLEDGE/      # Programming languages & concepts
└── 010_AGENTS/         # Agent integration docs & skills
```

## Learning Prompts

To teach your AI about new concepts and store them in your vault:

```
"Learn about [topic] and save it to my vault"
"Create a note about [concept] with examples in Python and JavaScript"
"Research [technology] and summarize it in my Knowledge folder"
"Explain [topic] in simple terms and add it to my Areas/Coding notes"
```

## Security Reminders
- Your `.env` file contains API keys — **never commit or share it**
- The AI can execute code and access files — review before trusting
- Use `F4` to mute JARVIS microphone during private conversations
- Review `SECURITY.md` for complete security guidelines
""", encoding="utf-8")

    # Prompt templates
    prompts_dir = vault_dir / "020_DASHBOARDS"
    prompts_dir.mkdir(exist_ok=True)
    (prompts_dir / "_PROMPT_TEMPLATES.md").write_text("""# Prompt Templates

## Code Generation
```
Write a [language] script that [task]
Include error handling and comments
Save the output to [path]
```

## Code Review
```
Review this [language] code for bugs, security issues, and improvements:
[code]
```

## Learning
```
Teach me about [topic] step by step
Include practical examples
Add a note to my vault in [folder]
```

## Debugging
```
I'm getting this error in [language]:
[error]
Here's my code:
[code]
Fix it and explain what was wrong.
```

## Project Planning
```
Plan a [type] project with:
- Tech stack: [technologies]
- Features: [list]
- Timeline: [estimate]
Create notes for each phase in my Projects folder.
```
""", encoding="utf-8")

    ok("User guides and prompt templates created")

    # Repos & Skills reference
    repos_ref = vault_dir / "003_RESOURCES" / "Tools" / "_REPOS_AND_SKILLS.md"
    repos_ref.write_text(f"""# Repositories, Skills & Plugins

## Core Repositories

| Repository | Purpose | URL |
|-----------|---------|-----|
| Mark-XXXV | Voice AI assistant | https://github.com/JARVIS-Systems/Mark-XXXV |
| OpenCode | CLI coding agent | https://github.com/anomalyco/opencode |
| AI Engine | Local LLM inference | (built from source) |
| Obsidian | Knowledge management | https://obsidian.md |

## Recommended Plugins (Obsidian)
1. **Obsidian Git** — Auto-backup vault to GitHub
2. **Dataview** — Query and aggregate notes
3. **Templater** — Advanced templates with variables
4. **Kanban** — Project boards
5. **Calendar** — Daily note calendar
6. **Tasks** — Task management with dates

## Suggested Add-ons
- **Ollama** — Run local models with a simple API (https://ollama.ai)
- **LM Studio** — GUI for GGUF models (https://lmstudio.ai)
- **Docker Desktop** — Containerized development (https://docker.com)
- **Windows Terminal** — Better terminal experience (Microsoft Store)

## Skills Categories
- **JARVIS skills**: Tool declarations in `main.py`, planner/executor in `agent/`
- **OpenCode skills**: Skill files in `models/opencode/skills/`
- **AI Engine plugins**: Python plugins in `models/ai_engine/plugins/`
- **Vault skills**: Custom skill docs in `010_AGENTS/Skills/`
""", encoding="utf-8")

    ok("Repo & skills reference created")
    return True


# ─── Phase 9: Final Validation ──────────────────────────────────────────────

def phase_final_validation():
    step("Phase 9/9: Running Final Validation")

    checks = []
    models_dir = SELF_DIR / "models"

    # Check Mark-XXXV
    jarvis_main = models_dir / "Mark-XXXV" / "main.py"
    checks.append(("JARVIS main.py", jarvis_main.exists()))

    # Check AI Engine
    ai_main = models_dir / "ai_engine" / "main.py"
    checks.append(("AI Engine main.py", ai_main.exists()))

    # Check config
    system_config = SELF_DIR / "config" / "system.json"
    checks.append(("System config", system_config.exists()))

    # Check vault
    vault_check = Path.home() / "Desktop" / "Shared Brain"
    checks.append(("Obsidian vault", vault_check.exists() and vault_check.is_dir()))

    # Check README
    checks.append(("README.md", (SELF_DIR / "README.md").exists()))
    checks.append(("SECURITY.md", (SELF_DIR / "SECURITY.md").exists()))

    # Python syntax check on all .py files
    py_files = list(SELF_DIR.rglob("*.py"))
    valid = 0
    invalid = 0
    for f in py_files:
        if "__pycache__" in str(f):
            continue
        try:
            compile(f.read_text(encoding="utf-8", errors="ignore"), str(f), "exec")
            valid += 1
        except SyntaxError:
            invalid += 1
    checks.append((f"Python syntax check ({valid} valid, {invalid} errors)", invalid == 0))

    # Report
    print()
    print(f"  {'Check':<45} {'Status':<10}")
    print(f"  {'-'*45} {'-'*10}")
    all_pass = True
    for name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:<45} {status:<10}")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        ok("ALL VALIDATIONS PASSED")
    else:
        warn("Some checks failed — review above")

    return all_pass


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║     MARK XXXV — Complete System Bootstrap Installer  ║")
    print("  ║  Voice AI + Local Engine + OpenCode + Shared Vault  ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print()
    print(f"  Install target: {SELF_DIR}")
    print()

    desktop = Path.home() / "Desktop"
    start = time.time()

    phases = [
        ("System Check", phase_system_check),
        ("Clone Components", lambda: phase_clone_repos(desktop)),
        ("Build AI Engine", lambda: phase_build_ai_engine(desktop)),
        ("Install Dependencies", phase_install_deps),
        ("Create Shared Brain Vault", lambda: phase_create_vault(desktop)),
        ("Install Skills & Plugins", lambda: phase_install_skills(desktop / "Shared Brain")),
        ("Unified Integration", lambda: phase_unified_integration(desktop / "Shared Brain")),
        ("User Guides & Prompts", lambda: phase_create_guides(desktop, desktop / "Shared Brain")),
        ("Final Validation", phase_final_validation),
    ]

    results = []
    for phase_name, phase_fn in phases:
        try:
            result = phase_fn()
            results.append((phase_name, result if isinstance(result, bool) else True))
            if isinstance(result, bool) and not result:
                warn(f"Phase '{phase_name}' reported failure")
        except Exception as e:
            results.append((phase_name, False))
            warn(f"Phase '{phase_name}' crashed: {e}")

        # Re-validate AI engine after build phase
        if phase_name == "Build AI Engine":
            engine_dir = SELF_DIR / "models" / "ai_engine"
            if engine_dir.exists():
                phase_validate_ai_engine(engine_dir)

    elapsed = time.time() - start

    # Final summary
    print()
    print(f"  {'='*60}")
    print(f"  INSTALLATION COMPLETE ({elapsed:.0f}s)")
    print(f"  {'='*60}")
    print()

    for name, passed in results:
        icon = "✅" if passed else "❌"
        print(f"  {icon}  {name}")

    print()
    print(f"  📍  System installed at: {SELF_DIR}")
    print(f"  📓  Vault at: {desktop / 'Shared Brain'}")
    print()
    print(f"  Next steps:")
    print(f"  1. Open Obsidian and open the 'Shared Brain' vault")
    print(f"  2. Create your .env file with GEMINI_API_KEY")
    print(f"  3. Run: python models/Mark-XXXV/main.py   (for JARVIS)")
    print(f"  4. Run: opencode                           (for OpenCode)")
    print(f"  5. Say: 'What can you do?' to JARVIS")
    print()
    print(f"  📖  Read SECURITY.md for important safety information")
    print(f"  📖  Open QUICK_START.md for setup steps")
    print(f"  📖  Open USER_GUIDE.md for command reference")
    print()


if __name__ == "__main__":
    main()
