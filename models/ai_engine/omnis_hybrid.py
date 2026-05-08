"""
Omnis Hybrid LLM Engine
Uses: Phi-4 Mini, Qwen2.5 Coder (local) + Gemini Flash 2 (cloud fallback)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from hybrid_llm_engine import get_engine
    
    class OmnisHybridLLM:
        """Omnis wrapper using hybrid engine."""
        
        def __init__(self, use_cloud_fallback=True):
            self.engine = get_engine()
            self.use_cloud_fallback = use_cloud_fallback
            # Your existing models
            self.default_local = 'phi-4-mini'  # General + reasoning
            self.code_local = 'qwen2.5-coder'  # Code tasks
            self.fast_local = 'qwen2.5-coder'  # Fast responses
        
        def chat(self, messages, prefer_local=True, **kwargs):
            """Chat with smart routing."""
            if prefer_local:
                try:
                    task_type = self._detect_task(messages)
                    model = self._select_local_model(task_type)
                    print(f"[Omnis] Using local: {model}")
                    return self.engine.chat_local(model, messages, **kwargs)
                except Exception as e:
                    print(f"[WARN] Local failed: {e}")
                    if not self.use_cloud_fallback:
                        return f"[ERROR] Local failed, cloud fallback disabled: {e}"
            
            # Cloud fallback
            if self.use_cloud_fallback:
                try:
                    from llm_engine import chat as cloud_chat
                    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                    return cloud_chat(prompt)
                except Exception as e:
                    return f"[ERROR] Both local and cloud failed: {e}"
            
            return "[ERROR] No LLM available"
        
        def generate(self, prompt, prefer_local=True, task_type='general', **kwargs):
            """Generate text with smart routing."""
            if prefer_local:
                try:
                    model = self._select_local_model(task_type)
                    print(f"[Omnis] Using local: {model}")
                    return self.engine.generate_local(model, prompt, **kwargs)
                except Exception as e:
                    print(f"[WARN] Local failed: {e}")
            
            if self.use_cloud_fallback:
                try:
                    from llm_engine import chat as cloud_chat
                    return cloud_chat(prompt)
                except Exception as e:
                    pass
            
            return "[ERROR] Generation failed"
        
        def select_model_for_task(self, task_type):
            """Select best model for task (matching OpenCode style)."""
            model_map = {
                'code': self.code_local,  # Qwen2.5 Coder
                'search': self.fast_local,  # Fast for summaries
                'define': self.default_local,  # Phi-4 Mini
                'research': self.code_local,  # Qwen for research
                'launch': self.fast_local,  # Fast response
                'general': self.default_local  # Phi-4 Mini
            }
            return model_map.get(task_type, self.default_local)
        
        def _select_local_model(self, task_type):
            """Select local model based on task."""
            return self.select_model_for_task(task_type)
        
        def _detect_task(self, messages):
            """Detect task type from messages."""
            if not messages:
                return 'general'
            
            last_msg = messages[-1].get('content', '').lower()
            
            if any(kw in last_msg for kw in ['code:', 'write', 'function', 'script']):
                return 'code'
            elif any(kw in last_msg for kw in ['search:', 'research:']):
                return 'search'
            elif any(kw in last_msg for kw in ['define:']):
                return 'define'
            elif any(kw in last_msg for kw in ['launch:']):
                return 'launch'
            
            return 'general'
        
        def get_status(self):
            """Get status."""
            return self.engine.get_status()
    
    _omnis_hybrid = None
    
    def get_omnis_hybrid():
        global _omnis_hybrid
        if _omnis_hybrid is None:
            _omnis_hybrid = OmnisHybridLLM()
        return _omnis_hybrid

except ImportError as e:
    print(f"[WARN] Hybrid engine not available: {e}")
    
    class OmnisHybridFallback:
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
        
        def get_status(self):
            return {'hybrid_available': False}
    
    def get_omnis_hybrid():
        return OmnisHybridFallback()


if __name__ == "__main__":
    ollm = get_omnis_hybrid()
    
    print("=== Omnis Hybrid LLM Test ===")
    print(f"Status: {ollm.get_status()}")
    print()
    
    # Test chat
    messages = [
        {"role": "system", "content": "You are OMNIS, a helpful AI assistant."},
        {"role": "user", "content": "What is Python?"}
    ]
    
    print("Test 1: General chat (should use Phi-4 Mini)")
    response = ollm.chat(messages, prefer_local=True, max_tokens=150)
    print(f"Response:\n{response}\n")
    
    # Test code task
    messages[-1]['content'] = "code: Write a Python fibonacci function"
    
    print("Test 2: Code task (should use Qwen2.5 Coder)")
    response = ollm.chat(messages, prefer_local=True, max_tokens=200)
    print(f"Response:\n{response}")
