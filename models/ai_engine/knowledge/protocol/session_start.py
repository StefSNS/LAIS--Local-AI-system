"""
OpenCode Session Start Protocol
Auto-executed at the beginning of every session.
Injects memory context (~180 tokens) for session continuity.
"""

import sys
from pathlib import Path

# Add Omnis to Python path
OMNIS_PATH = Path("%USERPROFILE%/Desktop/AI projects/Projects/Omnis")
sys.path.insert(0, str(OMNIS_PATH))

def execute_protocol():
    """Run this at session start to inject context."""
    try:
        from knowledge.memory.unified_memory import load_memory
        
        # Load memory with this agent's name
        mem = load_memory("opencode")
        
        # Generate context prompt (~180 tokens)
        context_prompt = mem.inject_context_prompt()
        
        # Display to user
        print(context_prompt)
        print("\n" + "="*50)
        print(f"Memory loaded: {mem.get_stats()}")
        print("="*50 + "\n")
        
        return context_prompt
        
    except Exception as e:
        print(f"[Protocol] Error: {e}")
        return None

if __name__ == "__main__":
    execute_protocol()
