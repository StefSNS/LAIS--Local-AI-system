"""
OpenCode Integration - Bridge between LAIS/Jarvis and OpenCode CLI agent.
Provides vault-aware context injection, crystallization, and local LLM access
for the OpenCode CLI agent in the 3-agent system (LAIS + Jarvis + OpenCode).
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

UNIFIED_LAYER_PATH = Path(r"str(Path(__file__).resolve().parent.parent)")
if str(UNIFIED_LAYER_PATH) not in sys.path:
    sys.path.insert(0, str(UNIFIED_LAYER_PATH))

opencode_unified = None
_local_llm = None

try:
    from unified_layer import load_unified_layer
    opencode_unified = load_unified_layer("opencode")
except Exception as e:
    print(f"[OpenCode] Unified layer load error: {e}")

try:
    from unified_layer.local_llm import get_local_llm
    _local_llm = get_local_llm()
except Exception:
    _local_llm = None


def get_vault_context(query="", max_tokens=200):
    """Get vault context for a query - use in system prompts."""
    if not opencode_unified:
        return ""
    return opencode_unified.get_context_injection(query, max_tokens=max_tokens)


def process_conversation(user_message, ai_response):
    """Process conversation through unified pipeline."""
    if not opencode_unified:
        return []
    return opencode_unified.process_conversation(user_message, ai_response)


def search_vault(query, max_results=5):
    """Search the Unified Brain vault."""
    if not opencode_unified:
        return []
    return opencode_unified.semantic_search(query, max_results=max_results)


def get_vault_stats():
    """Get vault statistics."""
    if not opencode_unified:
        return {}
    return opencode_unified.get_vault_stats()


def create_note(title, content, folder="00_Inbox"):
    """Create a new note in the vault."""
    if not opencode_unified:
        return None
    return opencode_unified.crystallization.create_vault_note(title, content, folder)


def crystallize_insight(key, value):
    """Add insight to crystallized knowledge."""
    if not opencode_unified:
        return
    opencode_unified.crystallization.crystallize_insight(key, value, source="opencode")


def local_ask(question, model=None, max_tokens=512):
    """Quick Q&A using local model."""
    if not _local_llm:
        return "[Local LLM unavailable]"
    return _local_llm.ask(question, model=model, max_tokens=max_tokens)


def local_code(prompt, model=None, language="python", max_tokens=1024):
    """Code generation using local model."""
    if not _local_llm:
        return "[Local LLM unavailable]"
    return _local_llm.code(prompt, language=language, model=model, max_tokens=max_tokens)


def local_chat(messages, model=None, max_tokens=512):
    """Full chat using local model."""
    if not _local_llm:
        return "[Local LLM unavailable]"
    return _local_llm.chat(messages, model=model, max_tokens=max_tokens)


def local_status():
    """Get local model status."""
    if not _local_llm:
        return {"available": False}
    return {"available": True, "model": getattr(_local_llm, "model_name", "unknown")}


if __name__ == "__main__":
    print("=== OpenCode Unified Layer Integration ===")
    stats = get_vault_stats()
    if stats:
        print(f"Notes: {stats.get('notes', 'N/A')}")
        print(f"Folders: {stats.get('folders', 'N/A')}")
        print(f"Crystallized: {stats.get('crystallized_items', 'N/A')}")
    context = get_vault_context("Python best practices")
    print(f"\nVault context for 'Python best practices':")
    print(context[:200] if context else "(none)")
