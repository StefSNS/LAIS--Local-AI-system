"""
Local LLM Engine - Optimized for your existing models
Leverages: Phi-4 Mini, Qwen2.5 Coder, and Gemini Flash 2
"""
import os
import json
from pathlib import Path

# Try to import local LLM support
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    print("[WARN] llama-cpp-python not installed")

# Try to import Gemini (already used by Jarvis)
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("[WARN] google.genai not available")


class HybridLLMEngine:
    """
    Hybrid engine: Uses local models when possible, falls back to Gemini Flash 2.
    Optimized for your existing setup:
    - Phi-4 Mini (reasoning/math)
    - Qwen2.5 Coder (code)
    - Gemini Flash 2 (Jarvis default, multimodal)
    """
    
    def __init__(self, models_dir="models"):
        self.models_dir = Path(models_dir)
        self.loaded_models = {}
        self.gemini_client = None
        
        # Initialize Gemini client (already configured in Jarvis)
        if GEMINI_AVAILABLE:
            try:
                api_key = self._get_gemini_api_key()
                if api_key:
                    genai.configure(api_key=api_key)
                    self.gemini_client = genai
                    print("[OK] Gemini client initialized")
            except Exception as e:
                print(f"[WARN] Gemini init failed: {e}")
    
    def _get_gemini_api_key(self):
        """Get Gemini API key from .env or environment."""
        import os
        from dotenv import load_dotenv
        
        # Load .env from LAIS directory
        env_path = Path(__file__).resolve().parent / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
        
        return os.environ.get("GEMINI_API_KEY", "")
    
    def get_model_path(self, model_name):
        """Find GGUF model file."""
        if not self.models_dir.exists():
            return None
        
        # Try different quantization patterns
        patterns = [
            f"{model_name}*q4_k_m.gguf",
            f"{model_name}*q4*.gguf",
            f"{model_name}*.gguf"
        ]
        
        import glob
        for pattern in patterns:
            matches = glob.glob(str(self.models_dir / pattern))
            if matches:
                return matches[0]
        return None
    
    def load_local_model(self, model_name, n_ctx=2048):
        """Load a local GGUF model."""
        if not LLAMA_AVAILABLE:
            return None
        
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        model_path = self.get_model_path(model_name)
        if not model_path:
            print(f"[WARN] Model not found: {model_name}")
            return None
        
        try:
            llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=0,  # CPU-only for 3GB RAM
                seed=1337,
                verbose=False
            )
            self.loaded_models[model_name] = llm
            print(f"[OK] Loaded local model: {model_name}")
            return llm
        except Exception as e:
            print(f"[ERROR] Failed to load {model_name}: {e}")
            return None
    
    def generate_local(self, model_name, prompt, max_tokens=512, temperature=0.7):
        """Generate using local model."""
        llm = self.load_local_model(model_name)
        if not llm:
            return None
        
        try:
            response = llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            print(f"[ERROR] Local generation failed: {e}")
            return None
    
    def generate_gemini(self, prompt, model="gemini-2.5-flash", max_tokens=512):
        """Generate using Gemini Flash 2 (Jarvis default)."""
        if not self.gemini_client:
            return None
        
        try:
            model = self.gemini_client.GenerativeModel(model)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[ERROR] Gemini generation failed: {e}")
            return None
    
    def smart_generate(self, prompt, task_type='general', prefer_local=True):
        """
        Smart routing: Uses local models when possible, Gemini for complex tasks.
        
        Args:
            prompt: Input prompt
            task_type: 'code', 'reasoning', 'general', 'vision'
            prefer_local: Try local first (default True for privacy/cost)
        
        Returns:
            Generated text
        """
        # Model mapping for your existing setup
        local_models = {
            'code': 'qwen2.5-coder',  # You already have this
            'reasoning': 'phi-4-mini',     # You already have this
            'math': 'phi-4-mini',
            'general': 'phi-4-mini',      # Default local
        }
        
        gemini_tasks = ['vision', 'multimodal', 'complex']
        
        # Use Gemini for vision/multimodal (it's better at this)
        if task_type in gemini_tasks:
            print(f"[Router] Using Gemini Flash 2 for {task_type}")
            result = self.generate_gemini(prompt)
            if result:
                return result
        
        # Try local first if preferred
        if prefer_local:
            model_key = local_models.get(task_type, 'phi-4-mini')
            print(f"[Router] Trying local model: {model_key}")
            result = self.generate_local(model_key, prompt)
            if result:
                return result
        
        # Fallback to Gemini
        print(f"[Router] Local failed, using Gemini Flash 2")
        return self.generate_gemini(prompt) or "[ERROR] All generation methods failed"
    
    def chat_local(self, model_name, messages, max_tokens=512):
        """Chat format using local model."""
        llm = self.load_local_model(model_name)
        if not llm:
            return None
        
        # Convert messages to prompt
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        try:
            response = llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"[ERROR] Local chat failed: {e}")
            return None
    
    def chat_gemini(self, messages, model="gemini-2.5-flash"):
        """Chat using Gemini."""
        if not self.gemini_client:
            return None
        
        try:
            # Convert messages to Gemini format
            prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            model = self.gemini_client.GenerativeModel(model)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[ERROR] Gemini chat failed: {e}")
            return None
    
    def smart_chat(self, messages, task_type='general', prefer_local=True):
        """Smart chat routing."""
        if prefer_local:
            model_key = {
                'code': 'qwen2.5-coder',
                'reasoning': 'phi-4-mini',
                'general': 'phi-4-mini'
            }.get(task_type, 'phi-4-mini')
            
            result = self.chat_local(model_key, messages)
            if result:
                return result
        
        return self.chat_gemini(messages) or "[ERROR] Chat failed"
    
    def unload_model(self, model_name):
        """Unload model to free RAM."""
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]
            print(f"[OK] Unloaded: {model_name}")
    
    def get_status(self):
        """Get engine status."""
        import psutil
        
        return {
            'loaded_local_models': list(self.loaded_models.keys()),
            'gemini_available': self.gemini_client is not None,
            'ram_available_gb': psutil.virtual_memory().available / (1024**3),
            'total_ram_gb': psutil.virtual_memory().total / (1024**3),
        }


# Singleton
_engine = None

def get_engine():
    """Get or create the singleton engine."""
    global _engine
    if _engine is None:
        _engine = HybridLLMEngine()
    return _engine


if __name__ == "__main__":
    engine = get_engine()
    
    print("=== Hybrid LLM Engine Test ===")
    print(f"Status: {engine.get_status()}")
    print()
    
    # Test with existing models
    test_prompt = "What is Python programming?"
    
    print(f"Test prompt: {test_prompt}")
    print("-" * 50)
    
    # Try local first
    result = engine.smart_generate(test_prompt, task_type='general')
    print(f"Result:\n{result}")
