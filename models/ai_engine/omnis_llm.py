"""
Omnis LLM Engine - Local-first with cloud fallback
Uses llama-cpp-python for local inference
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from local_llm_engine import get_engine, LocalLLMEngine
    
    class OmnisLLMEngine:
        """Omnis-specific LLM wrapper with cloud fallback."""
        
        def __init__(self, use_cloud_fallback=True):
            self.engine = get_engine()
            self.use_cloud_fallback = use_cloud_fallback
            self.default_model = 'qwen3-4b'  # Best for Omnis (code + general)
            self.fast_model = 'qwen2.5-coder-1.5b'  # Fast responses
            self.reasoning_model = 'phi-4-mini'  # Math/reasoning
        
        def chat(self, messages, use_local=True, **kwargs):
            """Chat with local-first, cloud fallback."""
            if use_local and self.engine:
                try:
                    return self.engine.chat(self.default_model, messages, **kwargs)
                except Exception as e:
                    print(f"[WARN] Local LLM failed: {e}")
                    if not self.use_cloud_fallback:
                        return f"[ERROR] Local LLM failed and cloud fallback disabled: {e}"
            
            # Cloud fallback - use original llm_engine
            if self.use_cloud_fallback:
                try:
                    from llm_engine import chat as cloud_chat
                    # Convert messages to single prompt
                    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                    return cloud_chat(prompt)
                except Exception as e:
                    return f"[ERROR] Both local and cloud LLM failed: {e}"
            
            return "[ERROR] No LLM available"
        
        def generate(self, prompt, use_local=True, model_type='general', **kwargs):
            """Generate text with model selection."""
            model_map = {
                'general': self.default_model,
                'fast': self.fast_model,
                'reasoning': self.reasoning_model,
                'code': 'qwen3-4b'
            }
            
            model_name = model_map.get(model_type, self.default_model)
            
            if use_local and self.engine:
                try:
                    return self.engine.generate(model_name, prompt, **kwargs)
                except Exception as e:
                    print(f"[WARN] Local generation failed: {e}")
            
            # Fallback
            if self.use_cloud_fallback:
                try:
                    from llm_engine import chat as cloud_chat
                    return cloud_chat(prompt)
                except Exception as e:
                    pass
            
            return "[ERROR] Generation failed"
        
        def select_model_for_task(self, task_type):
            """Auto-select best model for task type."""
            task_models = {
                'code': 'qwen3-4b',
                'search': 'qwen2.5-coder-1.5b',  # Fast for search summaries
                'define': 'phi-4-mini',  # Good for definitions
                'research': 'qwen3-4b',  # Better for research
                'launch': self.fast_model,  # Fast response
            }
            return task_models.get(task_type, self.default_model)
    
    # Singleton
    _omnis_llm = None
    
    def get_omnis_llm():
        global _omnis_llm
        if _omnis_llm is None:
            _omnis_llm = OmnisLLMEngine()
        return _omnis_llm

except ImportError as e:
    print(f"[WARN] Local LLM engine not available: {e}")
    
    class OmnisLLMFallback:
        """Fallback to original cloud LLM."""
        def chat(self, messages, **kwargs):
            try:
                from llm_engine import chat
                prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                return chat(prompt)
            except Exception as e:
                return "[ERROR] Could not load any LLM"
        
        def generate(self, prompt, **kwargs):
            try:
                from llm_engine import chat
                return chat(prompt)
            except Exception as e:
                return "[ERROR] Could not load any LLM"
        
        def select_model_for_task(self, task_type):
            return 'cloud'
    
    def get_omnis_llm():
        return OmnisLLMFallback()


if __name__ == "__main__":
    # Test
    ollm = get_omnis_llm()
    
    print("Testing Omnis LLM integration...")
    
    # Test chat
    messages = [
        {"role": "system", "content": "You are OMNIS, a helpful AI assistant."},
        {"role": "user", "content": "What is Python?"}
    ]
    
    response = ollm.chat(messages, max_tokens=150)
    print(f"\nChat response:\n{response}")
    
    # Test task-specific model selection
    task = 'code'
    model = ollm.select_model_for_task(task)
    print(f"\nSelected model for '{task}': {model}")
