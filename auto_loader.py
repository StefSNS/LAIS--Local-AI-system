#!/usr/bin/env python3
"""
LAIS Auto-Loader
Session auto-loader for token optimization and session continuity.
Loads vault context, crystallized learnings, and previous session state.
"""
import os, sys, json
from pathlib import Path
from datetime import datetime

LAIS_ROOT = Path(__file__).resolve().parent
VAULT_PATH = LAIS_ROOT / "vault"
UNIFIED_LAYER = LAIS_ROOT / "models" / "ai_engine" / "unified_layer"

class SessionTracker:
    def __init__(self):
        self.session_file = VAULT_PATH / "50_Memory" / "opencode_sessions.json"
        self.memory_db = LAIS_ROOT / "models" / "ai_engine" / "knowledge" / "memory" / "unified_memory.db"
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now()

    def load_sessions(self):
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r') as f:
                    return json.load(f)
            except: pass
        return []

    def save_session(self, context_size=0, summary=""):
        sessions = self.load_sessions()
        sessions.append({
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "context_size": context_size,
            "summary": summary,
            "duration": (datetime.now() - self.start_time).seconds
        })
        if len(sessions) > 50:
            sessions = sessions[-50:]
        try:
            with open(self.session_file, 'w') as f:
                json.dump(sessions, f, indent=2)
        except: pass

    def get_latest_session(self):
        sessions = self.load_sessions()
        return sessions[-1] if sessions else None

class TokenOptimizerLoader:
    def __init__(self):
        self.libraries = {}
        self.check_libraries()

    def check_libraries(self):
        for name, module in {"claw-compactor": "claw_compactor", "llmlingua": "llmlingua", "tokenpruner": "tokenpruner", "shekel": "shekel"}.items():
            try:
                __import__(module)
                self.libraries[name] = True
                print(f"[TOKEN] {name}: AVAILABLE")
            except ImportError:
                self.libraries[name] = False

    def init_optimizer(self, agent_name="lais"):
        try:
            sys.path.insert(0, str(UNIFIED_LAYER))
            from token_optimizer import get_token_optimizer
            return get_token_optimizer(agent_name)
        except ImportError:
            return None

def run_session_start_protocol():
    print("=" * 60)
    print("LAIS Session Start Protocol")
    print("=" * 60)
    print("\n[1/5] Loading session tracker...")
    st = SessionTracker()
    latest = st.get_latest_session()
    if latest: print(f"    Previous session: {latest.get('timestamp', 'unknown')}")

    print("\n[2/5] Loading memory layers...")
    crystallized = VAULT_PATH / "50_Memory" / "crystallized.json"
    count = 0
    if crystallized.exists():
        try:
            with open(crystallized) as f:
                count = len(json.load(f))
        except: pass
    print(f"    Crystallized learnings: {count}")

    print("\n[3/5] Initializing token optimizer...")
    tl = TokenOptimizerLoader()
    available = [k for k, v in tl.libraries.items() if v]
    print(f"    Available: {', '.join(available) if available else 'None (fallback mode)'}")

    print("\n[4/5] Loading vault context...")
    folders = []
    if VAULT_PATH.exists():
        folders = [str(p.relative_to(VAULT_PATH)) for p in VAULT_PATH.glob("*") if p.is_dir()]
    print(f"    Vault sections: {len(folders)}")

    print("\n[5/5] Initializing optimizer...")
    opt = tl.init_optimizer("opencode")
    print(f"    Token optimizer: {'READY' if opt else 'FALLBACK MODE'}")

    print("\n" + "=" * 60)
    print("Session Start Complete")
    print("=" * 60)
    return st

if __name__ == "__main__":
    run_session_start_protocol()
    print("\n[READY] LAIS is initialized and ready for use")
