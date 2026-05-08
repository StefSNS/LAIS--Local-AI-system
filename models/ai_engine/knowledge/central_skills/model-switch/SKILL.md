---
name: model-switch
description: Switch between local GGUF models. Use when user asks to switch models, change the AI model, or select phi3/qwen.
---

# Model Switch Skill

## When to Use

- User asks to "switch to phi3" or "use phi-3"
- User asks to "switch model" or "change model"
- User asks "what models available"

## Available Models

| Model | Context | Best For |
|-------|---------|---------|
| qwen | 4096 | Fast, general chat |
| phi3 | 4096 | Reasoning, instruction following |
| phi3_hybrid | 4096 | Memory-heavy tasks |

## Usage

**Check current model:**
```python
from llm_engine import get_current_model
print(get_current_model())
```

**Switch model:**
```python
from llm_engine import switch_model
switch_model("phi3")
```

**List models:**
```python
from llm_engine import get_available_models
print(get_available_models())
```

## Model Selection Criteria (AI Engineer Roadmap)

| Scenario | Recommended Model | Why |
|----------|-------------------|-----|
| General chat, quick answers | Qwen | Fast inference, efficient |
| Code review, debugging | Phi-3 | Better reasoning, instruction following |
| Long conversations, context-heavy | Phi-3 Hybrid | Optimized for memory tasks |
| System design, architecture | Phi-3 | Strong reasoning capabilities |
| API design, documentation | Phi-3 | Instruction following |

## Context Engineering (from roadmap)
- **System prompt**: Define role, behavior, constraints
- **Few-shot examples**: Provide 2-3 examples in prompt
- **Context window**: Max 4096 tokens (current config)
- **Prompt caching**: Reuse static context across calls
- **Structured output**: Request JSON for parseable responses

## Switching Models

**Check current model:**
```python
from llm_engine import get_current_model
print(get_current_model())
```

**Switch model:**
```python
from llm_engine import switch_model
switch_model("phi3")
```

**List models:**
```python
from llm_engine import get_available_models
print(get_available_models())
```

## Benefits
- **Qwen**: Fast, lighter on RAM
- **Phi-3**: Better reasoning
- **Phi-3 Hybrid**: Best for memory-intensive tasks