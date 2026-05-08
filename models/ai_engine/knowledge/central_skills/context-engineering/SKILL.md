---
name: context-engineering
description: Manage system prompts, context windows, RAG, and prompt optimization. Use when user asks about context, prompts, memory, RAG, or system messages.
---

# Context Engineering Skill

Based on roadmap.sh AI Engineer roadmap - Context Engineering section.

## When to Use
- User asks about "system prompt", "context window"
- User wants to "optimize prompts", "reduce tokens"
- Working with RAG (Retrieval Augmented Generation)
- Managing conversation history/memory
- Implementing prompt caching

## Context Engineering Components

### 1. System Prompt
```
You are [role].
Your goal: [objective].
Constraints: [rules].
Output format: [format].
```

### 2. Input Format
- **Few-shot examples**: Provide 2-3 examples in prompt
- **Structured input**: JSON/XML for clarity
- **Delimiters**: Use ``` or <tag> to separate sections

### 3. Context Management
| Strategy | When to Use | Benefit |
|----------|-------------|---------|
| **Prompt Caching** | Reuse static context | Reduces token costs |
| **Context Compaction** | Long conversations | Summarize old messages |
| **Context Isolation** | Multiple concerns | Prevent interference |
| **External Memory** | Persistent state | RAG, databases |
| **RAG (Retrieval)** | Large knowledge base | Fetch relevant docs |

### 4. Output Format
```python
# Request structured output
response = llm_engine.chat(
    messages=messages,
    response_format={"type": "json_object"}
)
```

### 5. Function Calling
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Search documentation",
            "parameters": {...}
        }
    }
]
```

## RAG Implementation

### Pipeline
```
Query → Embed → Vector Search → Retrieve Context → LLM → Response
```

### When to Use RAG
- Large knowledge base (>context window)
- Frequently updated information
- Need citations/sources
- Domain-specific knowledge

### Vector Databases (from roadmap)
| Database | Best For |
|----------|----------|
| **Chroma** | Local, simple setup |
| **Pinecone** | Managed, scalable |
| **Weaviate** | Production, multi-modal |
| **Qdrant** | Rust-based, fast |

## Token Optimization

### Context Window (Current: 4096 tokens)
- **Compress old messages**: Summarize to key points
- **Remove redundant context**: Deduplicate
- **Use references**: "As discussed earlier [ref]"
- **Streaming**: Handle token-by-token for long outputs

### Prompt Caching Strategy
```python
# Static context (cache this)
SYSTEM_PROMPT = "You are..."
PROJECT_CONTEXT = "Project uses..."

# Dynamic context (don't cache)
user_message = "Current question..."
```

## Guidelines
- Keep system prompt <500 tokens for efficiency
- Use few-shot examples for complex tasks
- Implement RAG for knowledge > context window
- Cache static context across calls
- Monitor token usage per request
