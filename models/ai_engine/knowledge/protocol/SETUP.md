# Session Start Protocol - Setup Instructions

## Auto-Execute at Session Start

### Option 1: Add to OpenCode Config (Recommended)

Create/Edit `config.json` in Omnis root:

```json
{
  "session_start": {
    "enabled": true,
    "script": "%USERPROFILE%/Desktop/AI projects/Projects/Omnis/knowledge/protocol/session_start.py",
    "auto_run": true
  }
}
```

### Option 2: Bash Profile (Windows PowerShell)

Add to your PowerShell profile (`$PROFILE`):

```powershell
# OpenCode Session Start Protocol
$protocol_script = "%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\protocol\session_start.py"
if (Test-Path $protocol_script) {
    python $protocol_script
}
```

### Option 3: Manual Command (Simplest)

At the start of every session, type:

```
/run protocol
```

Or create a bash alias in OpenCode:

```bash
alias protocol="python %USERPROFILE%/Desktop/AI\ projects/Projects/Omnis/knowledge/protocol/session_start.py"
```

## What the Protocol Does

1. **Loads `unified_memory.py`** (v2.0)
2. **Restores from previous session** (if exists)
3. **Injects context prompt** (~180 tokens):
   - Crystallized knowledge (5 items)
   - Projects state
   - Session summary
   - Unused skills reminder
4. **Displays memory stats**

## Token Usage

| Component | Tokens |
|-----------|--------|
| Crystallized (5 items) | ~50 |
| Session summary | ~30 |
| Projects state | ~30 |
| Agent info | ~20 |
| **Total** | **~130** |

(Well under the 180 token budget)

## Verify It Works

Run manually:
```bash
python "%USERPROFILE%/Desktop/AI projects/Projects/Omnis/knowledge/protocol/session_start.py"
```

Expected output:
```
<session_context>
LEARINGS:
- omnis_project_state: Major implementations complete...
...
</session_context>
Memory loaded: {'session_id': '...', 'agent': 'opencode', ...}
```

## Hard-Code Option (Alternative)

If you want me to ALWAYS inject context at the start of MY responses,
add this to my system prompt / instructions:

```
At the start of every session:
1. Run: python "%USERPROFILE%/Desktop/AI projects/Projects/Omnis/knowledge/protocol/session_start.py"
2. Use the injected context to inform all responses
```

## Files Created

- `session_start.py` - The protocol script
- `SETUP.md` (this file) - Instructions

## Next Session

The protocol will auto-load:
- ✅ Crystallized knowledge (5 items)
- ✅ Previous session context
- ✅ Project states
- ✅ Unused skills reminder
- ✅ Agent registry update

**Token cost: ~130 tokens (vs ~10,000+ without protocol)**
