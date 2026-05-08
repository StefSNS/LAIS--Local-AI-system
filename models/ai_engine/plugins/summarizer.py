import os
import json

SUMMARY_FILE = "knowledge/chat_summary.json"

def generate_summary(history_text):
    from llm_engine import chat
    """Summarize the conversation so far."""
    prompt = f"Summarize the key goals and facts from this conversation history so far. Keep it under 200 words:\n\n{history_text}"
    summary = chat(prompt)
    
    data = {
        "last_updated": __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M"),
        "content": summary
    }
    
    with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return summary

def get_current_summary():
    """Retrieve the stored summary."""
    if os.path.exists(SUMMARY_FILE):
        try:
            with open(SUMMARY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get("content", "")
        except Exception as e:
            return ""
    return "New project initiated."