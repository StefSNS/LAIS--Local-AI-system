import os
import json
from datetime import datetime

HISTORY_DIR = "knowledge/chat_history"
MAX_MESSAGES = 50
_today_cache = None
_today_date = None

def ensure_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)

def get_today_file():
    return os.path.join(HISTORY_DIR, f"session_{datetime.now().strftime('%Y-%m-%d')}.json")

def load_today():
    global _today_cache, _today_date
    today = datetime.now().strftime("%Y-%m-%d")
    
    if _today_cache is not None and _today_date == today:
        return _today_cache
    
    filepath = get_today_file()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            _today_cache = json.load(f)
            _today_date = today
            return _today_cache
    except Exception as e:
        _today_cache = {"date": today, "messages": []}
        _today_date = today
        return _today_cache

def save_message(role, content):
    global _today_cache
    history = load_today()
    
    history["messages"].append({
        "role": role,
        "content": content[:1000],
        "time": datetime.now().strftime("%H:%M:%S")
    })
    
    if len(history["messages"]) > MAX_MESSAGES:
        history["messages"] = history["messages"][-MAX_MESSAGES:]
    
    ensure_dir()
    with open(get_today_file(), 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def get_recent_context(n=5):
    history = load_today()
    recent = history["messages"][-n:]
    
    if not recent:
        return "[No previous messages]"
    
    ctx = []
    for msg in recent:
        prefix = "U" if msg["role"] == "user" else "O"
        ctx.append(f"{prefix}: {msg['content'][:100]}")
    
    return " | ".join(ctx)

def get_recent_messages(n=10):
    history = load_today()
    recent = history["messages"][-n:]
    
    if not recent:
        return []
    
    messages = []
    for msg in recent:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({
            "role": role,
            "content": msg.get("content", "")
        })
    
    return messages