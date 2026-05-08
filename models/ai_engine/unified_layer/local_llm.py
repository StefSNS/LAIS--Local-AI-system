"""
Local LLM Module for Unified Layer
Shared inference engine for Jarvis, AI Engine, and OpenCode.
Uses llama.cpp server for SmolLM3-3B and Qwen3-1.7B.
"""
import subprocess
import time
import requests
import os
import json
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
LLAMA_BIN = os.path.join(MODELS_DIR, "llama-bin")

MODEL_REGISTRY = {
    "smol3": {
        "path": os.path.join(MODELS_DIR, "HuggingFaceTB_SmolLM3-3B-Q4_K_M.gguf"),
        "label": "SmolLM3-3B",
        "ram": "~2.2GB",
        "best_for": "general, reasoning, quality",
    },
    "qwen3": {
        "path": os.path.join(MODELS_DIR, "Qwen3-1.7B-Q4_K_M.gguf"),
        "label": "Qwen3-1.7B",
        "ram": "~1.5GB",
        "best_for": "fast, coding, math",
    },
}


class LocalLLM:
    def __init__(self, agent_name="shared"):
        self.agent_name = agent_name
        self.loaded_models = {}
        self._servers = {}
        self._ports = {}
        self._next_port = 8100
        self._llama_server = os.path.join(LLAMA_BIN, "llama-server.exe")

        if not os.path.exists(self._llama_server):
            print(f"[LocalLLM] WARNING: llama-server.exe not found at {self._llama_server}")

    def _get_port(self, model_name):
        if model_name not in self._ports:
            self._ports[model_name] = self._next_port
            self._next_port += 1
        return self._ports[model_name]

    def _url(self, model_name):
        return f"http://127.0.0.1:{self._get_port(model_name)}"

    def is_loaded(self, model_name):
        if model_name not in self._servers:
            return False
        try:
            r = requests.get(f"{self._url(model_name)}/v1/models", timeout=1)
            return r.status_code == 200
        except Exception as e:
            return False

    def load(self, model_name):
        if model_name not in MODEL_REGISTRY:
            return False
        if self.is_loaded(model_name):
            return True

        model = MODEL_REGISTRY[model_name]
        if not os.path.exists(model["path"]):
            print(f"[LocalLLM:{self.agent_name}] Model missing: {model['label']}")
            return False
        if not os.path.exists(self._llama_server):
            print(f"[LocalLLM:{self.agent_name}] llama-server.exe missing")
            return False

        port = self._get_port(model_name)
        cmd = [
            self._llama_server,
            "-m", model["path"],
            "--port", str(port),
            "-c", "4096",
            "-t", "4",
            "--host", "127.0.0.1",
            "--log-disable",
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self._servers[model_name] = proc

            for _ in range(40):
                try:
                    r = requests.get(f"{self._url(model_name)}/v1/models", timeout=1)
                    if r.status_code == 200:
                        self.loaded_models[model_name] = model
                        print(f"[LocalLLM:{self.agent_name}] {model['label']} @ port {port}")
                        return True
                except Exception as e:
                    time.sleep(0.5)
            return True
        except Exception as e:
            print(f"[LocalLLM:{self.agent_name}] Start error: {e}")
            return False

    @staticmethod
    def _clean_response(text):
        if not text:
            return ""
        # Strip <think>...</think> tags
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        # Strip  tags
        text = re.sub(r'', '', text, flags=re.DOTALL).strip()
        # Strip internal monologue patterns
        text = re.sub(r'^Okay,?\s+(the\s+user|let\s+me|i\s+need|i\s+should|i\s+want|so\s+you).*?[\n.!?]', '', text, flags=re.IGNORECASE).strip()
        text = re.sub(r'^(First,?\s+I\s+should|First,\s+let|To\s+start,?\s+I)', '', text, flags=re.IGNORECASE).strip()
        # If the text is mostly monologue, try to extract the actual answer
        lines = text.split('\n')
        actual_lines = []
        skipping = True
        for line in lines:
            stripped = line.strip()
            if skipping:
                if len(stripped) > 30 and not any(kw in stripped.lower() for kw in ['i should', 'let me', 'i need', 'first,', 'okay,', 'hmm', 'wait', 'actually']):
                    skipping = False
            if not skipping:
                actual_lines.append(line)
        if actual_lines:
            text = '\n'.join(actual_lines).strip()
        return text

    def chat(self, messages, model="smol3", temperature=0.7, max_tokens=512):
        if not self.is_loaded(model):
            if not self.load(model):
                return None
        try:
            resp = requests.post(
                f"{self._url(model)}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=120,
            )
            if resp.status_code == 200:
                data = resp.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content", "")
                reasoning = msg.get("reasoning_content", "")
                # Combine: use content first, fall back to reasoning
                text = content if content.strip() else reasoning
                return self._clean_response(text) or None
            return None
        except Exception as e:
            return None
 
    def generate(self, prompt, model="smol3", system="", temperature=0.7, max_tokens=512):
        messages = [{"role": "user", "content": prompt}]
        if system:
            messages.insert(0, {"role": "system", "content": system})
        return self.chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)

    def ask(self, question, model="qwen3", max_tokens=384):
        """Quick single-turn Q&A."""
        return self.generate(question, model=model, max_tokens=max_tokens)

    def code(self, prompt, model="qwen3", language="python", max_tokens=512):
        """Code generation with optimized system prompt."""
        system = f"You are an expert {language} programmer. Write clean, well-commented code. Use markdown code blocks."
        return self.generate(prompt, model=model, system=system, max_tokens=max_tokens)

    def status(self):
        return {
            name: {
                "label": info["label"],
                "loaded": self.is_loaded(name),
                "downloaded": os.path.exists(info["path"]),
            }
            for name, info in MODEL_REGISTRY.items()
        }

    def available_models(self):
        return list(MODEL_REGISTRY.keys())

    def unload(self, model_name):
        if model_name in self._servers:
            try:
                self._servers[model_name].terminate()
            except Exception as e:
                pass
            del self._servers[model_name]
            self.loaded_models.pop(model_name, None)

    def unload_all(self):
        for name in list(self._servers.keys()):
            self.unload(name)


_instance = None


def get_local_llm(agent_name="shared"):
    global _instance
    if _instance is None:
        _instance = LocalLLM(agent_name)
    return _instance


if __name__ == "__main__":
    llm = get_local_llm("test")
    print("=== Local LLM Test ===")
    print(f"Models: {llm.available_models()}")
    print(f"Status: {llm.status()}")

    print("\nQwen3 (fast):")
    r = llm.ask("What is Python in 10 words?", model="qwen3")
    print(r or "(failed)")

    print("\nSmolLM3 (quality):")
    r = llm.ask("Explain recursion briefly", model="smol3")
    print(r or "(failed)")

    print("\nCode generation:")
    r = llm.code("fibonacci function", model="qwen3")
    print(r or "(failed)")

    llm.unload_all()
