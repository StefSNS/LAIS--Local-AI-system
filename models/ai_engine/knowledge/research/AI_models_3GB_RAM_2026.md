# AI Models for 3GB RAM - Research Report 2026

## Executive Summary

After deep research, I've identified the best AI models that can run efficiently in ~3GB RAM for integration with Jarvis (Mark-XXXV), Omnis, and OpenCode.

---

## Top Recommended Models (3GB RAM or less)

### 1. **Gemma 3n E4B-IT** - Best Multimodal Option
- **Parameters**: 8B (nested/efficient architecture)
- **Size**: ~3GB (Q4_K_M quantization)
- **Capabilities**: Text, image, audio multimodal
- **RAM Required**: ~3GB
- **Use Case**: Best for Jarvis voice + vision tasks
- **Source**: Google DeepMind (Apache 2.0)
- **Link**: https://huggingface.co/google/gemma-3n-e4b-it

### 2. **Qwen3-4B** - Best for Code + Reasoning
- **Parameters**: 4B
- **Size**: ~2.6GB (Q4_K_M)
- **Capabilities**: 92 programming languages, reasoning, math
- **RAM Required**: ~3GB
- **Use Case**: Best for Omnis code tasks, OpenCode
- **Source**: Alibaba Cloud (Apache 2.0)
- **Link**: https://huggingface.co/Qwen/Qwen3-4B

### 3. **Phi-4 Mini** - Best for Reasoning/Math
- **Parameters**: 3.8B
- **Size**: ~2.5GB (Q4_K_M)
- **Capabilities**: Strong reasoning, math, analytical tasks
- **RAM Required**: ~3GB
- **Use Case**: Best for complex reasoning in all systems
- **Source**: Microsoft (MIT License)
- **Link**: https://huggingface.co/microsoft/phi-4-mini-reasoning

### 4. **Qwen2.5 Coder 1.5B** - Best Tiny Code Model
- **Parameters**: 1.5B
- **Size**: ~1.2GB (Q4_K_M)
- **Capabilities**: 92 languages, HumanEval 43.3%
- **RAM Required**: ~1.5GB
- **Use Case**: Lightweight code completion
- **Source**: Alibaba Cloud (Apache 2.0)
- **Link**: https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B

### 5. **Llama 3.2 3B** - Meta's Efficient Model
- **Parameters**: 3B
- **Size**: ~3.5GB (Q4_K_M)
- **Capabilities**: General purpose, good quality/size ratio
- **RAM Required**: ~3.5GB
- **Use Case**: General tasks across all systems
- **Source**: Meta (Llama 3 License)
- **Link**: https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct

### 6. **SmolLM3-3B** - Ultra-Compact
- **Parameters**: 3B
- **Size**: ~2GB (Q4_K_M)
- **Capabilities**: Fast inference, edge-optimized
- **RAM Required**: ~2.5GB
- **Use Case**: Edge devices, fast responses
- **Source**: Hugging Face (Apache 2.0)
- **Link**: https://huggingface.co/HuggingFaceTB/SmolLM3-3B

---

## Quantization Options for 3GB RAM

| Quantization | Bits | Size (7B model) | Quality | Best For |
|--------------|------|------------------|---------|-----------|
| **Q4_K_M** | 4-bit | ~3.8GB | Excellent | **Recommended default** |
| **Q4_K_S** | 4-bit | ~3.6GB | Good | Low RAM systems |
| **IQ4_XS** | 4-bit | ~3.4GB | Very Good | CPU-friendly |
| **Q3_K_M** | 3-bit | ~3.1GB | Good | Tight RAM |
| **IQ3_M** | 3-bit | ~3.0GB | Better 3-bit | High-quality 3-bit |
| **Q3_K_S** | 3-bit | ~2.8GB | Lower | Extreme compression |
| **Q2_K** | 2-bit | ~2.7GB | Low | Minimum viable |

**Recommendation**: Use **Q4_K_M** for best balance, or **IQ3_M** if RAM is very tight.

---

## Integration Strategy for Jarvis + Omnis + OpenCode

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Unified Model Manager                    │
│  (llama.cpp / llama-cpp-python)                  │
├─────────────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Gemma 3 │  │ Qwen3-4B│  │ Phi-4   │    │
│  │ (Voice/  │  │ (Code/  │  │ (Reasoning│    │
│  │ Vision) │  │ General)│  │ /Math)  │    │
│  └──────────┘  └──────────┘  └──────────┘    │
│       ↓               ↓               ↓             │
│  ┌──────────────────────────────────────┐      │
│  │     Task Router & Model Selector        │      │
│  └──────────────────────────────────────┘      │
│                    ↓                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Jarvis  │  │ Omnis   │  │OpenCode │  │
│  │ (Voice   │  │ (GUI     │  │ (CLI    │  │
│  │ Chat)   │  │ Chat)   │  │ Chat)   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Integration Approach

#### 1. **For Jarvis (Mark-XXXV) - Voice-First**
- **Primary Model**: Gemma 3n E4B-IT (multimodal: voice + vision)
- **Integration**: Replace Gemini API with local GGUF model
- **Benefits**: No API costs, privacy, offline capability
- **Code**: `actions/local_llm.py` using `llama-cpp-python`

```python
# Jarvis integration example
from llama_cpp import Llama

class LocalLLMEngine:
    def __init__(self):
        self.models = {
            'voice': Llama(model_path='models/gemma-3n-e4b-q4_k_m.gguf'),
            'code': Llama(model_path='models/qwen3-4b-q4_k_m.gguf'),
            'reasoning': Llama(model_path='models/phi-4-mini-q4_k_m.gguf')
        }
    
    def generate(self, prompt, task_type='voice'):
        model = self.models.get(task_type, self.models['voice'])
        return model(prompt, max_tokens=512, temperature=0.7)
```

#### 2. **For Omnis - GUI-First**
- **Primary Model**: Qwen3-4B (code + general)
- **Integration**: Replace `llm_engine.py` Qwen model with local GGUF
- **Benefits**: Faster responses, no cloud dependency
- **Code**: Modify `llm_engine.py` to use `llama-cpp-python`

```python
# Omnis integration example
from llama_cpp import Llama

def chat(prompt, model_name='qwen3-4b-q4_k_m.gguf'):
    llm = Llama(
        model_path=f"models/{model_name}",
        n_ctx=4096,
        n_gpu_layers=-1  # Use GPU if available
    )
    response = llm(prompt, max_tokens=2048)
    return response['choices'][0]['text']
```

#### 3. **For OpenCode - CLI-First**
- **Primary Model**: Qwen2.5 Coder 1.5B (tiny, fast)
- **Integration**: Use as default model for code tasks
- **Benefits**: Sub-second responses, minimal RAM usage
- **Code**: Direct integration in OpenCode's tool chain

---

## Implementation Plan

### Phase 1: Setup llama.cpp Python Bindings (Day 1)
```bash
# Install llama-cpp-python (includes llama.cpp build)
pip install llama-cpp-python

# Download models (3GB RAM optimized)
# Option 1: Gemma 3n E4B (multimodal)
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='google/gemma-3n-e4b-it', allow_patterns=['*q4_k_m.gguf'], local_dir='models')"

# Option 2: Qwen3-4B (code + general)
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Qwen/Qwen3-4B', allow_patterns=['*q4_k_m.gguf'], local_dir='models')"

# Option 3: Phi-4 Mini (reasoning)
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='microsoft/phi-4-mini-reasoning', allow_patterns=['*q4_k_m.gguf'], local_dir='models')"
```

### Phase 2: Jarvis Integration (Day 2-3)
1. Create `actions/local_llm.py` with `llama-cpp-python`
2. Modify `main.py` to optionally use local models
3. Add model selection logic based on task type
4. Test voice interaction with Gemma 3n

### Phase 3: Omnis Integration (Day 4-5)
1. Modify `llm_engine.py` to support both cloud and local models
2. Add model switcher (GUI dropdown)
3. Test GUI chat with Qwen3-4B
4. Benchmark response times vs cloud models

### Phase 4: OpenCode Integration (Day 6-7)
1. Add local model support to OpenCode's tool chain
2. Default to Qwen2.5 Coder 1.5B for code tasks
3. Add `/model` command to switch models
4. Test CLI interaction

### Phase 5: Unified Model Manager (Day 8-10)
1. Create shared `model_manager.py` for all systems
2. Implement task-based model routing
3. Add memory-efficient model swapping
4. Create unified API that all three systems use

---

## Workflow Optimization Examples

### Example 1: Jarvis Voice Task
```
User: "JARVIS, what's the weather in Paris?"
↓
Task Router: weather_query (simple)
↓
Model Selected: Gemma 3n E4B (multimodal capable)
↓
local_llm.generate("Weather in Paris?")
↓
Response: "Sir, Paris is currently 18°C with light rain..."
```

### Example 2: Omnis Code Task
```
User: "code: create a Python script for fibonacci"
↓
Task Router: code_generation
↓
Model Selected: Qwen3-4B (92 languages supported)
↓
local_llm.generate("Write fibonacci in Python...")
↓
Response: "Here's a Python fibonacci implementation..."
```

### Example 3: OpenCode Quick Task
```
> search: latest Python best practices
↓
Task Router: web_search (use plugin)
↓
Fallback: Qwen2.5 Coder 1.5B for summary
↓
Response: "Here are the latest Python best practices..."
```

---

## Memory & Performance Tips

### RAM Management
- **Keep 1-2GB free** for OS and other apps
- **Use Q4_K_M** for best quality/size ratio
- **Unload models** when switching (llama.cpp handles this)
- **Context window**: Reduce to 2048 tokens if RAM is tight

### Speed Optimization
- **GPU layers**: Set `n_gpu_layers=-1` if you have GPU
- **CPU only**: Use `IQ4_XS` or `Q4_K_S` for faster CPU inference
- **Batch size**: Reduce to 128 for lower RAM usage

### Model Swapping Strategy
```python
# Efficient model swapping
def get_model_for_task(task_type):
    model_map = {
        'vision': 'gemma-3n-e4b-q4_k_m.gguf',
        'code': 'qwen3-4b-q4_k_m.gguf',
        'reasoning': 'phi-4-mini-q4_k_m.gguf',
        'fast': 'qwen2.5-coder-1.5b-q4_k_m.gguf'
    }
    return model_map.get(task_type, model_map['fast'])
```

---

## File Structure for Implementation

```
%USERPROFILE%\Desktop\AI projects\
├── Projects\
│   ├── LocalClaw\models\Mark-XXXV\
│   │   ├── actions\local_llm.py          # NEW: Local LLM integration
│   │   ├── models\                       # NEW: GGUF models directory
│   │   └── main.py                      # MODIFY: Add local model support
│   │
│   └── Omnis\
│       ├── llm_engine_local.py           # NEW: Local LLM engine
│       ├── models\                       # NEW: GGUF models directory
│       └── llm_engine.py                   # MODIFY: Add local model option
│
└── Models\                              # Shared models directory
    ├── gemma-3n-e4b-q4_k_m.gguf     # 3GB - Multimodal
    ├── qwen3-4b-q4_k_m.gguf          # 2.6GB - Code + General
    ├── phi-4-mini-q4_k_m.gguf        # 2.5GB - Reasoning
    └── qwen2.5-coder-1.5b-q4_k_m.gguf # 1.2GB - Tiny code
```

---

## Benchmarks (Estimated for 3GB RAM Systems)

| Model | RAM Usage | Tokens/sec (CPU) | Tokens/sec (GPU) | Quality |
|-------|-----------|-------------------|-------------------|---------|
| Gemma 3n E4B Q4 | ~3.0GB | ~15 tok/s | ~45 tok/s | ★★★★☆ |
| Qwen3-4B Q4 | ~2.6GB | ~18 tok/s | ~50 tok/s | ★★★★☆ |
| Phi-4 Mini Q4 | ~2.5GB | ~20 tok/s | ~55 tok/s | ★★★☆☆ |
| Qwen2.5 Coder 1.5B Q4 | ~1.2GB | ~35 tok/s | ~80 tok/s | ★★★☆☆ |
| Llama 3.2 3B Q4 | ~3.5GB | ~16 tok/s | ~48 tok/s | ★★★☆☆ |

---

## Recommended Quick Start

For **immediate testing** with minimal setup:

1. **Install llama-cpp-python**:
   ```bash
   pip install llama-cpp-python
   ```

2. **Download Qwen2.5 Coder 1.5B** (smallest, fastest):
   ```bash
   # From Hugging Face (requires huggingface_hub)
   python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-Coder-1.5B', allow_patterns=['*q4_k_m.gguf'], local_dir='models')"
   ```

3. **Test in Python**:
   ```python
   from llama_cpp import Llama
   llm = Llama(model_path='models/qwen2.5-coder-1.5b-q4_k_m.gguf')
   print(llm("Write a Python function to calculate fibonacci", max_tokens=256)['choices'][0]['text'])
   ```

4. **Integrate with Jarvis/Omnis** using the code examples above.

---

## Conclusion

- **Best Overall**: Gemma 3n E4B-IT (multimodal, ~3GB)
- **Best for Code**: Qwen3-4B or Qwen2.5 Coder 1.5B
- **Best for Reasoning**: Phi-4 Mini
- **Integration**: Use `llama-cpp-python` for all three systems
- **Next Step**: Download one model and test with provided code examples

**Time Spent**: ~25 minutes (within 20-30 min budget)
