import os
import sys
from pathlib import Path

LAIS_PATH = Path(r"str(Path(__file__).resolve().parent)")
sys.path.insert(0, str(LAIS_PATH))

results = []

def test(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((status, name, detail))
    print(f"[{status}] {name}" + (f" - {detail}" if detail else ""))

# 1. Jarvis SQLite DB - no duplicates
import sqlite3
JARVIS_DB = os.environ.get("JARVIS_MEMORY_DB", r"%USERPROFILE%\Desktop\AI projects\Mark-XXXV\memory\jarvis_memory.db")
conn = sqlite3.connect(JARVIS_DB)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM memory_entries")
total_rows = cur.fetchone()[0]
cur.execute("SELECT DISTINCT category, key, value FROM memory_entries")
unique_rows = len(cur.fetchall())
test("Jarvis DB duplicates cleaned", total_rows == unique_rows, f"total={total_rows}, unique={unique_rows}")
conn.close()

# 2. LAIS unified memory has Jarvis entries
conn = sqlite3.connect(r"str(Path(__file__).resolve().parent)\knowledge\memory\unified_memory.db")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM memory_entries")
omnis_total = cur.fetchone()[0]
test("Omnis unified memory has entries", omnis_total >= 5, f"total={omnis_total}")
conn.close()

# 3. Vault notes exist and are indexed
from pathlib import Path
vault_path = Path(os.environ.get("LAIS_VAULT_PATH", r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain"))
user_profile = vault_path / "40_System" / "user_profile.md"
project_states = vault_path / "40_System" / "project_states.md"
agent_registry = vault_path / "40_System" / "agent_registry.md"
test("user_profile.md exists", user_profile.exists())
test("project_states.md exists", project_states.exists())
test("agent_registry.md exists", agent_registry.exists())

# 4. Unified layer loads with all components
from unified_layer import load_unified_layer
layer = load_unified_layer("opencode")
test("Unified layer loads", layer is not None)
test("Protocol layer active", layer.protocols is not None)
test("Gateway layer active", layer.gateway is not None)
test("Orchestrator active", layer.orchestrator is not None)
test("Token optimizer active", hasattr(layer, 'token_optimizer') and layer.token_optimizer is not None)

# 5. Context injection includes new vault data
ctx = layer.get_context_injection("user preferences", max_tokens=500, session_start=True)
test("Context injection works", len(ctx) > 0, f"context length={len(ctx)}")

# 6. Vault search finds new notes
search_results = layer.index.search_notes("user profile preferences", max_results=5)
test("Vault search finds user_profile", any("user_profile" in r.get("path", "") for r in search_results), f"found {[r.get('path','') for r in search_results]}")

search_results = layer.index.search_notes("project states ecommerce", max_results=5)
test("Vault search finds project_states", any("project_states" in r.get("path", "") for r in search_results), f"found {[r.get('path','') for r in search_results]}")

# 7. Shared memory sync v2
try:
    from unified_layer.memory_sync_v2 import SharedMemoryStoreV2
    sync = SharedMemoryStoreV2()
    
    # Store from opencode
    entry_id = sync.store("opencode", "test_verification", "Integration verified", "test", priority="high")
    test("Sync v2 store works", entry_id is not None, f"entry_id={entry_id}")
    
    # Retrieve as jarvis
    entry = sync.retrieve(entry_id, "jarvis")
    test("Cross-agent retrieval works", entry is not None, f"retrieved={'yes' if entry else 'no'}")
    
    # Cross-agent search
    search = sync.cross_agent_search("Integration verified", limit=5)
    test("Cross-agent search works", len(search) > 0, f"results={len(search)}")
    
    # Cleanup
    sync.cleanup_expired()
    test("Cleanup runs without error", True)
    
except Exception as e:
    test("Shared memory sync v2", False, f"Error: {e}")

# 8. Full pipeline test
try:
    layer.process_conversation("What is the current project status?", "Based on vault context, projects are active.")
    test("Full pipeline: process_conversation", True)
    
    # Verify gateway captured the messages
    sessions = layer.gateway.list_sessions()
    test("Gateway captured session", len(sessions) > 0, f"sessions={len(sessions)}")
    
    # Verify protocol layer
    proto_status = layer.get_protocol_status()
    test("Protocol status check", proto_status.get("local_agents", 0) > 0, f"agents={proto_status.get('local_agents', 0)}")
    
    # Verify orchestrator classification
    classification = layer.classify_query("Build a REST API")
    test("Orchestrator classification works", classification is not None, f"classification={classification}")
    
except Exception as e:
    test("Full pipeline test", False, f"Error: {e}")

# 9. Token optimization
try:
    from unified_layer.token_optimizer import load_token_optimizer
    optimizer = load_token_optimizer("verify")
    tokens = optimizer.estimate_tokens("Test message for verification")
    test("Token optimizer works", tokens > 0, f"tokens={tokens}")
except Exception as e:
    test("Token optimizer", False, f"Error: {e}")

# Summary
passed = sum(1 for s, _, _ in results if s == "PASS")
failed = sum(1 for s, _, _ in results if s == "FAIL")
print(f"\n{'='*60}")
print(f"VERIFICATION SUMMARY: {passed}/{passed+failed} tests passed")
if failed > 0:
    print(f"\nFAILED TESTS:")
    for s, n, d in results:
        if s == "FAIL":
            print(f"  [FAIL] {n} - {d}")
print(f"{'='*60}")
