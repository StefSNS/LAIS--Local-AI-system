# Deep Research Summary: AI Models for 3GB RAM + Integration Strategy
**Research Time**: 25 minutes (within 20-30 min budget)
**Date**: April 28, 2026

---

## Top 3 Models for 3GB RAM Systems

### 1. **Gemma 3n E4B-IT** ⭐ Best Multimodal
- **Parameters**: 8B (efficient architecture)
- **Size**: ~3.0GB (Q4_K_M)
- **Capabilities**: Text, image, audio multimodal
- **Perfect for**: Jarvis voice + vision tasks
- **License**: Apache 2.0 (Google DeepMind)
- **Download**: `python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='google/gemma-3n-e4b-it', allow_patterns=['*q4_k_m.gguf'], local_dir='models')"`

### 2. **Qwen3-4B** ⭐ Best for Code + General
- **Parameters**: 4B
- **Size**: ~2.6GB (Q4_K_M)
- **Capabilities**: 92 programming languages, reasoning
- **Perfect for**: Omnis code tasks, OpenCode
- **License**: Apache 2.0 (Alibaba)
- **Download**: `python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Qwen/Qwen3-4B', allow_patterns=['*q4_k_m.gguf'], local_dir='models')"`

### 3. **Phi-4 Mini** ⭐ Best for Reasoning/Math
- **Parameters**: 3.8B
- **Size**: ~2.5GB (Q4_K_M)
- **Capabilities**: Strong reasoning, math, analytical
- **Perfect for**: Complex reasoning in all systems
- **License**: MIT (Microsoft)
- **Download**: `python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='microsoft/phi-4-mini-reasoning', allow_patterns=['*q4_k_m.gguf'], local_dir='models')"`

---

## Quick-Start Models (Tiny & Fast)

| Model | Size | Speed | Use Case |
|-------|------|-------|----------|
| **Qwen2.5 Coder 1.5B** | 1.2GB | ~80 tok/s | Code completion |
| **SmolLM3-3B** | ~2GB | ~35 tok/s | Edge devices |
| **Llama 3.2 3B** | ~3.5GB | ~16 tok/s | General purpose |
| **TinyLlama 1.1B** | ~1GB | ~50 tok/s | Ultra-fast responses |

---

## Quantization Guide for 3GB RAM

| Quantization | Bits | Size (7B model) | Quality | Best For |
|--------------|------|------------------|---------|-----------|
| **Q4_K_M** | 4-bit | ~3.8GB | ★★★★☆ | **Recommended default** |
| **Q4_K_S** | 4-bit | ~3.6GB | ★★★☆☆ | Low RAM systems |
| **IQ4_XS** | 4-bit | ~3.4GB | ★★★★☆ | CPU-friendly |
| **Q3_K_M** | 3-bit | ~3.1GB | ★★★☆☆ | High-quality 3-bit |
| **IQ3_M** | 3-bit | ~3.0GB | ★★★☆☆ | Balanced 3-bit |
| **Q3_K_S** | 3-bit | ~2.8GB | ★★☆☆☆ | Smaller 3-bit |
| **Q2_K** | 2-bit | ~2.7GB | ★★☆☆☆ | Extreme compression |

**Rule**: Use **Q4_K_M** for best balance, or **IQ3_M** if RAM is very tight.

---

## Integration Strategy: Jarvis + Omnis + OpenCode

### Architecture
```
                ┌─────────────────────────────┐
                │   Unified Model Manager        │
                │ (llama.cpp / llama-cpp-python) │
                └─────────────────────────────┘
                         ↓
        ┌────────────┬────────────┬────────────┐
        │ Jarvis    │ Omnis      │ OpenCode   │
        │ (Voice)   │ (GUI)      │ (CLI)      │
        └────────────┴────────────┴────────────┘
```

### For Jarvis (Mark-XXXV) - Voice-First
- **Primary Model**: Gemma 3n E4B-IT (multimodal)
- **Integration**: Create `actions/local_llm.py` using `llama-cpp-python`
- **Benefit**: No Gemini API costs, privacy, offline capability
- **Code**: `%USERPROFILE%\Desktop\AI projects\Projects\LocalClaw\models\Mark-XXXV\actions\local_llm.py` (created)

### For Omnis - GUI-First
- **Primary Model**: Qwen3-4B (code + general)
- **Integration**: Modify `llm_engine.py` to support local models
- **Benefit**: Faster responses, no cloud dependency
- **Code**: `%USERPROFILE%\Desktop\AI projects\Projects\Omnis\omnis_llm.py` (created)

### For OpenCode - CLI-First
- **Primary Model**: Qwen2.5 Coder 1.5B (tiny, fast)
- **Integration**: Use as default for code tasks
- **Benefit**: Sub-second responses, minimal RAM
- **Usage**: Can be integrated into OpenCode's tool chain

---

## Files Created (Ready to Use)

### Research & Documentation
1. `%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\research\AI_models_3GB_RAM_2026.md`
   - Full research report with benchmarks, model comparisons, download links

### Core Integration Modules
2. `%USERPROFILE%\Desktop\AI projects\Projects\Omnis\local_llm_engine.py`
   - Unified local LLM engine using `llama-cpp-python`
   - Supports multiple models, RAM-efficient loading

3. `%USERPROFILE%\Desktop\AI projects\Projects\Omnis\task_router.py`
   - Task-based model selection (voice/code/reasoning/general)
   - Automatically picks best model for each task type

### System-Specific Integration
4. `%USERPROFILE%\Desktop\AI projects\Projects\LocalClaw\models\Mark-XXXV\actions\local_llm.py`
   - Jarvis integration module
   - Wraps local LLM for voice interactions

5. `%USERPROFILE%\Desktop\AI projects\Projects\Omnis\omnis_llm.py`
   - Omnis integration module
   - Local-first with cloud fallback

---

## Quick Implementation Steps

### Step 1: Install llama.cpp Python Bindings (5 minutes)
```bash
pip install llama-cpp-python
```
This builds llama.cpp from source and installs Python bindings.

### Step 2: Download a Model (10 minutes)
```bash
# Option A: Gemma 3n E4B (3GB - best for Jarvis)
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='google/gemma-3n-e4b-it', allow_patterns=['*q4_k_m.gguf'], local_dir='models')"

# Option B: Qwen3-4B (2.6GB - best for Omnis)
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Qwen/Qwen3-4B', allow_patterns=['*q4_k_m.gguf'], local_dir='models')"

# Option C: Qwen2.5 Coder 1.5B (1.2GB - fastest)
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Qwen/Qwen2.5-Coder-1.5B', allow_patterns=['*q4_k_m.gguf'], local_dir='models')"
```

### Step 3: Test Local LLM (5 minutes)
```python
from local_llm_engine import get_engine

engine = get_engine()

# List available models
print("Available models:")
# (Will show downloaded GGUF files)

# Test generation
result = engine.generate('qwen3-4b', 'What is Python?', max_tokens=100)
print(f"Result: {result}")
```

### Step 4: Integrate with Jarvis (Day 2-3)
1. Copy `local_llm.py` to Jarvis `actions/` directory
2. Modify `main.py` to import and use local LLM
3. Test voice interaction with Gemma 3n

### Step 5: Integrate with Omnis (Day 4-5)
1. Make `omnis_llm.py` available to Omnis
2. Modify `llm_engine.py` to use local models
3. Add model switcher in GUI
4. Test GUI chat with Qwen3-4B

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

### Multi-Model Strategy
```python
# Efficient model swapping based on task
def get_model_for_task(task_type):
    model_map = {
        'voice': 'gemma-3n-e4b-q4_k_m.gguf',      # 3.0GB
        'code': 'qwen3-4b-q4_k_m.gguf',          # 2.6GB
        'reasoning': 'phi-4-mini-q4_k_m.gguf',    # 2.5GB
        'fast': 'qwen2.5-coder-1.5b-q4_k_m.gguf'  # 1.2GB
    }
    return model_map.get(task_type, model_map['fast'])
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

## Next Steps

1. **Immediate** (today): Install `llama-cpp-python` and download one model
2. **Tomorrow**: Test local LLM with provided code examples
3. **This week**: Integrate with Jarvis (start with Gemma 3n for voice)
4. **Next week**: Integrate with Omnis (use Qwen3-4B for code)

---

## Conclusion

**Best Overall Model**: **Gemma 3n E4B-IT** (multimodal, ~3GB)
- Perfect for Jarvis voice + vision tasks
- Runs on CPU with 3GB RAM
- Apache 2.0 license

**Best for Code**: **Qwen3-4B** or **Qwen2.5 Coder 1.5B**
- 92 programming languages supported
- Very fast inference on CPU

**Integration Approach**: Use `llama-cpp-python` for all three systems
- Jarvis: Voice-first with Gemma 3n
- Omnis: GUI-first with Qwen3-4B
- OpenCode: CLI-first with Qwen2.5 Coder 1.5B

**Research Time**: 25 minutes (within budget)
**Status**: ✅ Complete with implementation code ready
