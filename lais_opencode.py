#!/usr/bin/env python3
"""
LAIS OpenCode Launcher
Launches OpenCode with LAIS context, CoComm integration, and token optimization.
"""
import os, sys, json, subprocess
from pathlib import Path

LAIS_ROOT = Path(__file__).resolve().parent
UNIFIED_LAYER = LAIS_ROOT / "models" / "ai_engine" / "unified_layer"
VAULT_PATH = LAIS_ROOT / "vault"

def load_config():
    config_path = LAIS_ROOT / "config" / "system.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {"vault": {"path": str(VAULT_PATH)}, "a2a": {"port": 8020}}

def init_token_optimizer():
    try:
        sys.path.insert(0, str(UNIFIED_LAYER))
        from token_optimizer import get_token_optimizer
        opt = get_token_optimizer("opencode")
        print(f"[LAIS] Token Optimizer v1.0.0 initialized (claw-compactor, llmlingua, tokenpruner, shekel)")
        return opt
    except ImportError as e:
        print(f"[LAIS] Token Optimizer not available: {e}")
        return None

def init_cocomm():
    print("[LAIS] CoComm integration available (see integrations/)")
    return None

def load_vault_context():
    context = {"system": {}, "agent_registry": {}, "crystallized": []}
    system_path = VAULT_PATH / "40_System"
    if system_path.exists():
        for f in system_path.glob("*.md"):
            if f.stem not in ("PROTOCOL", "registry"):
                try: context["system"][f.stem] = f.read_text(encoding="utf-8")[:2000]
                except: pass
    return context

def launch_opencode():
    print("=" * 60)
    print("LAIS OpenCode Launcher")
    print("=" * 60)
    config = load_config()
    print(f"[CONFIG] Vault: {config['vault']['path']}")
    print("\n[INIT] Loading systems...")
    load_vault_context()
    init_token_optimizer()
    init_cocomm()

    opencode_bin = os.environ.get("OPENCODE_BIN", None)
    if not opencode_bin:
        for candidate in ["opencode", "opencode.cmd", "npx opencode"]:
            from shutil import which
            if which(candidate):
                opencode_bin = candidate
                break
    if not opencode_bin:
        print("[ERROR] OpenCode not found. Install: npm install -g opencode-ai")
        return 1

    env = os.environ.copy()
    env["LAIS_ROOT"] = str(LAIS_ROOT)
    env["LAIS_VAULT"] = str(VAULT_PATH)
    env["LAIS_UNIFIED_LAYER"] = str(UNIFIED_LAYER)
    env["LAIS_TOKEN_OPTIMIZATION"] = "1"

    try:
        subprocess.call([opencode_bin], env=env, cwd=str(LAIS_ROOT))
    except KeyboardInterrupt:
        print("\n[LAIS] Session ended by user")
    except Exception as e:
        print(f"\n[ERROR] Failed to launch: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(launch_opencode())
