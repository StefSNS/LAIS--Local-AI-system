"""
Local LLM Engine using llama-cpp-python
Provides unified interface for Jarvis, Omnis, and OpenCode
"""
import os
from pathlib import Path

try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    print("[WARN] llama-cpp-python not installed. Install with: pip install llama-cpp-python")


class LocalLLMEngine:
    """Unified local LLM engine for 3GB RAM systems."""
    
    def __init__(self, models_dir="models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.loaded_models = {}
        
    def get_model_path(self, model_name):
        """Get full path to GGUF model file."""
        # Try different quantization formats
        quants = ['q4_k_m.gguf', 'q4_k_s.gguf', 'q3_k_m.gguf', 'q2_k.gguf']
        
        for q in quants:
            path = self.models_dir / f"{model_name}-{q}"
            if path.exists():
                return str(path)
        
        # Try exact name
        path = self.models_dir / f"{model_name}.gguf"
        if path.exists():
            return str(path)
        
        return None
    
    def load_model(self, model_name, n_ctx=2048, n_gpu_layers=0):
        """Load a model. Returns Llama instance or None."""
        if not LLAMA_AVAILABLE:
            print("[ERROR] llama-cpp-python not available")
            return None
        
        model_path = self.get_model_path(model_name)
        if not model_path:
            print(f"[ERROR] Model not found: {model_name}")
            return None
        
        try:
            llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                seed=1337,
                verbose=False
            )
            self.loaded_models[model_name] = llm
            print(f"[OK] Loaded model: {model_name}")
            return llm
        except Exception as e:
            print(f"[ERROR] Failed to load {model_name}: {e}")
            return None
    
    def generate(self, model_name, prompt, max_tokens=512, temperature=0.7, **kwargs):
        """Generate text using specified model."""
        if model_name not in self.loaded_models:
            llm = self.load_model(model_name)
            if not llm:
                return f"[ERROR] Could not load model: {model_name}"
        else:
            llm = self.loaded_models[model_name]
        
        try:
            response = llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            return f"[ERROR] Generation failed: {e}"
    
    def chat(self, model_name, messages, max_tokens=512, **kwargs):
        """Chat format using messages list."""
        if model_name not in self.loaded_models:
            llm = self.load_model(model_name)
            if not llm:
                return f"[ERROR] Could not load model: {model_name}"
        else:
            llm = self.loaded_models[model_name]
        
        try:
            response = llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                **kwargs
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            return f"[ERROR] Chat failed: {e}"
    
    def unload_model(self, model_name):
        """Unload model to free RAM."""
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]
            print(f"[OK] Unloaded: {model_name}")


# Singleton instance
_engine = None

def get_engine():
    """Get or create the singleton engine."""
    global _engine
    if _engine is None:
        _engine = LocalLLMEngine()
    return _engine


if __name__ == "__main__":
    # Test the engine
    engine = get_engine()
    
    # List available models
    print("Available models:")
    if engine.models_dir.exists():
        for f in engine.models_dir.glob("*.gguf"):
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  - {f.stem} ({size_mb:.1f} MB)")
    
    # Test generation if models available
    if engine.loaded_models:
        test_prompt = "What is Python programming?"
        print(f"\nTest prompt: {test_prompt}")
        for name in engine.loaded_models:
            result = engine.generate(name, test_prompt, max_tokens=100)
            print(f"\n{name} response:\n{result}\n")
