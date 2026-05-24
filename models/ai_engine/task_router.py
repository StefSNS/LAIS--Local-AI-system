"""
Task Router for selecting optimal model based on task type
Works with 3GB RAM constraint - aligned with unified_layer/orchestrator.py
"""
import os
import sys
from pathlib import Path

# Add LAIS to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Model configurations - aligned with orchestrator MODEL_ENDPOINTS
# Resolve model directory: prefer LocalClaw (has full setup), fall back to local models/
_TR_BASE = Path(__file__).resolve().parent
_TR_MODELS_DIR = str(_TR_BASE.parent)
MODEL_CONFIGS = {
    'phi4': {
        'name': 'phi4',
        'label': 'Phi-4-mini-instruct (3.8B)',
        'path': os.path.join(_TR_MODELS_DIR, 'microsoft_Phi-4-mini-instruct-Q4_K_M.gguf'),
        'size_gb': 2.49,
        'best_for': ['reasoning', 'coding', 'instruction_following', 'analysis'],
        'context': 8192,
        'port': 8100,
        'n_gpu_layers': 0,
    },
    'qwen4': {
        'name': 'qwen4',
        'label': 'Qwen3.5-4B',
        'path': os.path.join(_TR_MODELS_DIR, 'Qwen3.5-4B-Q4_K_M.gguf'),
        'size_gb': 2.74,
        'best_for': ['code', 'general', 'fast_tasks', 'instruction_following'],
        'context': 4096,
        'port': 8101,
        'n_gpu_layers': 0,
    },
    'qwen3': {
        'name': 'qwen3',
        'label': 'Qwen3-1.7B',
        'path': os.path.join(_TR_MODELS_DIR, 'Qwen_Qwen3-1.7B-Q4_K_M.gguf'),
        'size_gb': 1.28,
        'best_for': ['general_chat', 'summarization', 'quick_tasks'],
        'context': 32768,
        'port': 8102,
        'n_gpu_layers': 0,
    },
}


class TaskRouter:
    """Route tasks to optimal model based on type and available RAM."""
    
    def __init__(self):
        self.engine = get_engine()
        self.loaded_models = []
    
    def route(self, task_type, prompt, **kwargs):
        """
        Route task to best model.
        
        Args:
            task_type: 'voice', 'code', 'reasoning', 'general', etc.
            prompt: The input prompt
            **kwargs: Additional generation params
        
        Returns:
            Generated text
        """
        model_name = self._select_model(task_type)
        
        if not model_name:
            return "[ERROR] No suitable model found for task type: {task_type}"
        
        return self.engine.generate(model_name, prompt, **kwargs)
    
    def _select_model(self, task_type):
        """Select best model for task type within 3GB RAM."""
        # Score each model for this task
        scores = []
        
        for model_key, config in MODEL_CONFIGS.items():
            score = 0
            
            # Check if model is good for this task
            if task_type in config['best_for']:
                score += 10
            elif 'general' in config['best_for']:
                score += 5
            
            # Prefer smaller models (leave RAM for OS)
            if config['size_gb'] <= 1.5:
                score += 3
            elif config['size_gb'] <= 2.5:
                score += 2
            elif config['size_gb'] <= 3.0:
                score += 1
            
            # Check if model exists
            model_path = self.engine.get_model_path(config['name'])
            if model_path:
                score += 5
                # Actually load the model
                if config['name'] not in self.loaded_models:
                    llm = self.engine.load_model(config['name'], n_ctx=config['context'], n_gpu_layers=config['n_gpu_layers'])
                    if llm:
                        self.loaded_models.append(config['name'])
            
            scores.append((score, model_key))
        
        # Sort by score (highest first)
        scores.sort(reverse=True)
        
        if scores:
            best_model = MODEL_CONFIGS[scores[0][1]]['name']
            print(f"[Router] Selected model: {best_model} for task: {task_type}")
            return best_model
        
        return None
    
    def chat(self, task_type, messages, **kwargs):
        """Chat format with automatic model selection."""
        model_name = self._select_model(task_type)
        
        if not model_name:
            return "[ERROR] No suitable model found"
        
        return self.engine.chat(model_name, messages, **kwargs)
    
    def get_status(self):
        """Get status of loaded models and RAM usage."""
        import psutil
        
        status = {
            'loaded_models': self.loaded_models,
            'available_models': list(MODEL_CONFIGS.keys()),
            'ram_available_gb': psutil.virtual_memory().available / (1024**3),
            'total_ram_gb': psutil.virtual_memory().total / (1024**3),
        }
        
        return status


if __name__ == "__main__":
    router = TaskRouter()
    
    # Test routing
    test_cases = [
        ('voice', "What's the weather in Paris?"),
        ('code', "Write a Python fibonacci function"),
        ('reasoning', "Solve: If x + 5 = 12, what is x?"),
        ('general', "Tell me about AI"),
    ]
    
    for task_type, prompt in test_cases:
        print(f"\n{'='*50}")
        print(f"Task: {task_type}")
        print(f"Prompt: {prompt}")
        result = router.route(task_type, prompt, max_tokens=100)
        print(f"Result:\n{result}\n")
