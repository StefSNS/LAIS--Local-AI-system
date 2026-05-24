import json
import sys
import os
import subprocess
import time
import threading
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 'plugins')
sys.path.insert(0, os.path.join(BASE_DIR, 'knowledge', 'memory'))
sys.path.insert(0, os.path.join(BASE_DIR, 'unified_layer'))

try:
    from unified_layer import load_unified_layer
    unified = load_unified_layer("lais")
except Exception as e:
    print(f"[llm_engine] Error loading unified layer: {e}")
    unified = None

try:
    from unified_memory import UnifiedMemory, load_memory
    mem = load_memory("lais")
except Exception as e:
    print(f"[llm_engine] Error loading unified memory: {e}")
    from memory_lais import DCTPMemory
    mem = DCTPMemory()

llamafile_path = os.path.join(BASE_DIR, "models", "llamafile.exe")
LLAMA_SERVER = None
LLAMA_CLI = None

def _find_llama_cpp_binaries():
    """Find llama.cpp server and CLI binaries."""
    global LLAMA_SERVER, LLAMA_CLI
    paths_to_check = [
        os.path.join(BASE_DIR, "models", "llama-bin"),
        os.path.join(os.path.dirname(BASE_DIR), "llama-bin"),
        os.path.join(os.path.dirname(BASE_DIR), "llama-bin"),
    ]
    for p in paths_to_check:
        server = os.path.join(p, "llama-server.exe")
        cli = os.path.join(p, "llama-cli.exe")
        if os.path.exists(server):
            LLAMA_SERVER = server
        if os.path.exists(cli):
            LLAMA_CLI = cli
        if LLAMA_SERVER and LLAMA_CLI:
            break

_find_llama_cpp_binaries()

_server_process = None
_server_port = 8080
_server_ready = False

OMNIS_IDENTITY = """You are LAIS, a highly capable and thoughtful AI assistant.

PERSONALITY:
- Be warm, conversational, and natural in your responses
- Show genuine interest in helping the user
- Use a professional but friendly tone
- Be concise when appropriate, but detailed when the situation calls for it
- Acknowledge context and follow-up naturally on previous discussion points

CAPABILITIES:
- You can answer questions, write and review code, research topics, manage files, and help with creative tasks
- You have access to a knowledge base with information about various topics
- You maintain memory across sessions and learn from interactions

RESPONSE GUIDELINES:
- Think step-by-step before answering complex questions
- If you're unsure, say so - don't fabricate information
- When helping with code, explain your reasoning
- Ask clarifying questions when the user's request is ambiguous
- Offer follow-up suggestions when relevant ("Would you like me to...?", "I can also help with...")
- Adapt your response length to match the complexity of the question
- Use markdown formatting for code blocks, lists, and emphasis when helpful

CONVERSATION STYLE:
- Treat this as an ongoing dialogue - reference earlier messages naturally
- Use phrases like "As we discussed earlier..." or "Following up on that..."
- Show understanding of the user's goals and preferences
- Be proactive: anticipate what the user might need next"""

def _load_config():
    config_path = os.path.join(BASE_DIR, "config.json")
    with open(config_path, "r") as f:
        return json.load(f)

def get_available_models():
    cfg = _load_config()
    models = cfg.get("models", {})
    return {k: v for k, v in models.items()}

def switch_model(model_name: str) -> bool:
    global _server_process, _server_ready
    
    models = get_available_models()
    if model_name not in models:
        return False
    
    cfg = _load_config()
    cfg["active_model"] = model_name
    cfg["model_path"] = models[model_name]["path"]
    cfg["n_ctx"] = cfg.get("n_ctx", 4096)
    cfg["n_threads"] = cfg.get("n_threads", 4)
    
    with open(os.path.join(BASE_DIR, "config.json"), "w") as f:
        json.dump(cfg, f, indent=2)
    
    if _server_process:
        _server_process.terminate()
        _server_process = None
        _server_ready = False
    
    return start_server()

def get_current_model():
    cfg = _load_config()
    return cfg.get("active_model", "phi3")

def start_server():
    global _server_process, _server_ready
    
    if _server_process is not None:
        return True
    
    cfg = _load_config()
    model_path = cfg.get("model_path", "")
    if not model_path:
        active = cfg.get("active_model", "smol3")
        models = cfg.get("models", {})
        if active in models:
            model_path = models[active]["path"]
    if not os.path.isabs(model_path):
        model_path = os.path.join(BASE_DIR, model_path)
    if not os.path.exists(model_path):
        print(f"[ERROR] Model not found: {model_path}")
        return False
    n_ctx = cfg.get("n_ctx", 4096)
    n_threads = cfg.get("n_threads", 4)
    
    if LLAMA_SERVER and os.path.exists(LLAMA_SERVER):
        cmd = [
            LLAMA_SERVER,
            "-m", model_path,
            "--port", str(_server_port),
            "-c", str(n_ctx),
            "-t", str(n_threads),
            "--host", "127.0.0.1",
            "--log-disable"
        ]
    else:
        cmd = [
            llamafile_path,
            "-m", model_path,
            "--server",
            "--port", str(_server_port),
            "-c", str(n_ctx),
            "-t", str(n_threads),
            "--host", "127.0.0.1"
        ]
    
    try:
        _server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        for _ in range(30):
            try:
                r = requests.get(f"http://127.0.0.1:{_server_port}/v1/models", timeout=1)
                if r.status_code == 200:
                    _server_ready = True
                    print(f"[LLM Server ready] ({cfg.get('active_model', 'unknown')})")
                    return True
            except Exception as e:
                time.sleep(0.5)
        
        return True
    except Exception as e:
        print(f"[Server start error: {e}]")
        return False

def _get_knowledge_context(query):
    try:
        if unified:
            vault_context = unified.get_context_injection(query, max_tokens=400)
            if vault_context:
                return vault_context
    except Exception as e:
        pass
    
    try:
        from knowledge_retriever import get_context
        knowledge = get_context(query)
        if knowledge and "[No relevant" not in knowledge:
            return knowledge[:500]
    except Exception as e:
        pass
    return ""

def _get_session_summary():
    try:
        if unified:
            return unified.get_context_injection("", max_tokens=200, session_start=True)
    except Exception as e:
        pass
    try:
        if hasattr(mem, 'inject_context_prompt'):
            return mem.inject_context_prompt()
    except Exception as e:
        pass
    return ""

def _get_recent_messages(n=10):
    try:
        from chat_history import get_recent_messages
        messages = get_recent_messages(n)
        return messages
    except Exception as e:
        try:
            from chat_history import get_recent_context
            recent = get_recent_context(n)
            if recent and "[No previous" not in recent:
                return recent
        except Exception as e:
            pass
    return ""

def _build_messages(user_input):
    knowledge = _get_knowledge_context(user_input)
    session_summary = _get_session_summary()
    recent_messages = _get_recent_messages(12)
    
    system_prompt = OMNIS_IDENTITY
    
    if knowledge:
        system_prompt += f"\n\nRELEVANT KNOWLEDGE:\n{knowledge}"
    
    if session_summary:
        system_prompt += f"\n\n{session_summary}"
    
    messages = [{"role": "system", "content": system_prompt}]
    
    if isinstance(recent_messages, list):
        for msg in recent_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": content})
    elif isinstance(recent_messages, str) and recent_messages:
        messages.append({"role": "user", "content": recent_messages})
    
    messages.append({"role": "user", "content": user_input})
    
    return messages

def chat(p):
    global _server_ready
    
    if _server_process is None:
        start_server()
    
    messages = _build_messages(p)
    
    try:
        if hasattr(mem, 'add_message'):
            mem.add_message("user", p)
    except Exception as e:
        try:
            mem.add(p, "T1")
        except Exception as e:
            pass
    
    try:
        response = requests.post(
            f"http://127.0.0.1:{_server_port}/v1/chat/completions",
            json={
                "model": "lais",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024,
                "stream": False
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            r = result["choices"][0]["message"]["content"]
        else:
            r = _fallback_chat(p)
            
    except Exception as e:
        r = _fallback_chat(p)
    
    try:
        from chat_history import save_message
        save_message("lais", r)
        if hasattr(mem, 'add_message'):
            mem.add_message("assistant", r)
        
        if unified:
            unified.process_conversation(p, r)
    except Exception as e:
        pass
    
    try:
        if hasattr(mem, 'save'):
            mem.save()
    except Exception as e:
        pass
    
    return r

def _fallback_chat(p):
    cfg = _load_config()
    model_path = cfg.get("model_path", "")
    if not model_path:
        active = cfg.get("active_model", "smol3")
        models = cfg.get("models", {})
        if active in models:
            model_path = models[active]["path"]
    if not os.path.isabs(model_path):
        model_path = os.path.join(BASE_DIR, model_path)
    n_ctx = cfg.get("n_ctx", 4096)
    n_threads = cfg.get("n_threads", 4)
    
    messages = _build_messages(p)
    prompt_str = json.dumps(messages)
    
    if LLAMA_CLI and os.path.exists(LLAMA_CLI):
        cmd = [
            LLAMA_CLI,
            "-m", model_path,
            "-p", prompt_str,
            "-c", str(n_ctx),
            "-t", str(n_threads),
            "-n", "1024",
            "--temp", "0.7",
            "--log-disable"
        ]
    else:
        cmd = [
            llamafile_path,
            "--cli",
            "-m", model_path,
            "-p", prompt_str,
            "-c", str(n_ctx),
            "-t", str(n_threads),
            "-n", "1024"
        ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            last_assistant = output.split(">")[-1].strip() if ">" in output else output
            return last_assistant if last_assistant else output
        else:
            return f"Error: {result.stderr.strip()[:100]}"
            
    except subprocess.TimeoutExpired:
        return "[Timeout - please try again]"
    except Exception as e:
        return f"[Error: {str(e)[:100]}]"

def stop_server():
    global _server_process
    if _server_process:
        _server_process.terminate()
        _server_process = None

if __name__ == "__main__":
    start_server()
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = chat(user_input)
        print(f"Omnis: {response}\n")
