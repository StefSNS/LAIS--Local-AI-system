"""
Memory Manager for JARVIS
Manages persistent user memory across sessions.
"""

import json
from pathlib import Path
from datetime import datetime

MEMORY_FILE = Path(__file__).parent.parent / "memory" / "user_memory.json"

def load_memory():
    """Load user memory from file."""
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text())
        except:
            pass
    return {}

def update_memory(update_dict):
    """Update memory with new data."""
    memory = load_memory()
    for category, values in update_dict.items():
        if category not in memory:
            memory[category] = {}
        memory[category].update(values)
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(memory, indent=2))

def format_memory_for_prompt(memory):
    """Format memory as string for system prompt."""
    if not memory:
        return ""
    lines = ["[USER MEMORY]"]
    for category, values in memory.items():
        lines.append(f"{category.upper()}:")
        for key, data in values.items():
            lines.append(f"  {key}: {data.get('value', '')}")
    return "\n".join(lines)