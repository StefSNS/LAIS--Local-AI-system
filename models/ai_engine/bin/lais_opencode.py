"""LAIS-aware OpenCode launcher — wraps OpenCode sessions with vault context, token optimization, and memory."""
import sys, json, os, subprocess, argparse
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "unified_layer"))

TOKEN_LOG = BASE / "knowledge" / "memory" / "opencode_sessions.json"
TOKEN_LOG.parent.mkdir(parents=True, exist_ok=True)

_unified = None
_token_opt = None


def _load_unified():
    global _unified, _token_opt
    if _unified is not None:
        return _unified
    try:
        from unified_layer import UnifiedLayer
        _unified = UnifiedLayer("opencode")
        try:
            from token_optimizer import get_token_optimizer
            _token_opt = get_token_optimizer("opencode")
        except Exception:
            _token_opt = None
        return _unified
    except Exception as e:
        print(f"[LAIS-OpenCode] Unified layer: {e}", file=sys.stderr)
        return None


def build_system_prompt(vault_context: str = "") -> str:
    ctx = _load_unified()
    parts = ["You are LAIS + OpenCode — a unified AI agent with access to the Obsidian vault."]

    if ctx:
        active = ctx.crystallization.get_active_state_context()
        if active:
            parts.append(f"\n## Active State\n{active}")

        crystal = ctx.crystallization.crystallized
        if crystal:
            items = "\n".join(f"- {c.get('key','')}: {c.get('value','')[:200]}" for c in crystal[-10:])
            parts.append(f"\n## Crystallized Knowledge\n{items}")

    if vault_context:
        parts.append(f"\n## Vault Context\n{vault_context}")

    parts.append("""
## Capabilities
- Read/write vault notes via UnifiedLayer
- Semantic search across the vault
- Persist insights to crystallized memory
- Access local LLM for offline tasks
- Token-optimized prompts (auto-compressed)
- Cross-agent via protocol layer

## Vault Structure
- 00_Inbox — new/draft notes
- 10_Resources — reference material
- 20_Skills — AGENTS.md + skill files
- 30_Research — research notes
- 30_Projects — project docs + Shared_Memory
- 40_System — architecture, protocols, templates
- 50_Memory — crystallized knowledge, decision logs

Use `lais://vault/search?q=<query>` for vault searches.
Use `lais://memory/save?key=<key>&value=<value>` to persist insights.
""")
    return "\n".join(parts)


def log_session(session_id: str, prompt_tokens: int = 0, response_tokens: int = 0):
    log = []
    if TOKEN_LOG.exists():
        try:
            log = json.loads(TOKEN_LOG.read_text(encoding="utf-8"))
        except Exception:
            log = []
    log.append({
        "session_id": session_id,
        "prompt_tokens": prompt_tokens,
        "response_tokens": response_tokens,
        "total_tokens": prompt_tokens + response_tokens,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    })
    TOKEN_LOG.write_text(json.dumps(log[-500:], indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="LAIS-aware OpenCode launcher")
    parser.add_argument("task", nargs="?", default="", help="Initial task for OpenCode")
    parser.add_argument("--vault-context", "-c", default="", help="Vault query for context injection")
    parser.add_argument("--no-vault", action="store_true", help="Skip vault context loading")
    parser.add_argument("--opencode-args", default="", help="Extra args for opencode binary")
    args = parser.parse_args()

    vault_context = ""
    if not args.no_vault:
        ctx = _load_unified()
        if ctx and args.vault_context:
            vault_context = ctx.get_context_injection(args.vault_context, max_tokens=200)
        elif ctx:
            vault_context = ctx.get_context_injection("system overview", max_tokens=200)

    prompt = build_system_prompt(vault_context)

    # Save system prompt for OpenCode to use
    prompt_file = BASE / "knowledge" / "memory" / "opencode_prompt.md"
    prompt_file.write_text(prompt, encoding="utf-8")
    print(f"[LAIS-OpenCode] System prompt written ({len(prompt.split())} words)", file=sys.stderr)

    if _token_opt:
        _token_opt.log_usage("session_start", len(prompt.split()), "session_start")
        _token_opt._save_log()

    log_session(__import__("uuid").uuid4().hex[:8], prompt_tokens=len(prompt.split()))

    opencode_args = args.opencode_args.split() if args.opencode_args else []
    cmd = ["opencode"] + opencode_args
    if args.task:
        cmd.append(args.task)

    print(f"[LAIS-OpenCode] Launching: {' '.join(cmd)}", file=sys.stderr)
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
