---
name: prompt-engineering
description: Design, test, and optimize prompts for LLMs. Use when user asks about prompt engineering, system prompts, few-shot examples, or chain-of-thought.
---

# Prompt Engineering Skill

## When to Use
- User asks about "prompt engineering", "system prompt"
- User wants to "optimize prompts", "reduce tokens"
- Designing prompts for specific models
- Implementing few-shot learning
- Adding chain-of-thought reasoning

## Core Concepts (from roadmap.sh/Prompt-Engineering)

### 1. System Prompt
Define the AI's role, behavior, constraints.
```
You are a Python expert. Your goal: Help write clean code.
Constraints: Always include type hints, follow PEP 8.
Output format: Provide code + explanation.
```

### 2. Few-Shot Prompting
Provide examples in the prompt.
```
Translate to French:
Example 1: "Hello" → "Bonjour"
Example 2: "Goodbye" → "Au revoir"
Now translate: "Thank you" →
```

### 3. Chain-of-Thought (CoT)
Encourage step-by-step reasoning.
```
Solve: What is 15% of 80?
Let me think step by step:
1. Convert 15% to decimal: 15/100 = 0.15
2. Multiply: 0.15 * 80 = 12
Answer: 12
```

### 4. Zero-Shot Prompting
Direct request without examples.
```
Classify: "I love this product!"
Sentiment: Positive
```

## Prompting Techniques

### Role Prompting
```
You are an expert {ROLE}. 
Think like a {ROLE} would.
```

### Delimiters
Use clear separators for complex inputs.
```
Summarize the following text:
---
{paste long text here}
---
Summary:
```

### Structured Output
Request specific format.
```python
# Request JSON
response = llm.chat(
    messages=[{"role": "user", "content": "Return JSON with name, age"}],
    response_format={"type": "json_object"}
)
```

## Model-Specific Strategies

| Model | Best Approach |
|-------|----------------|
| **Qwen** | Direct prompts, clear instructions |
| **Phi-3** | Few-shot examples, CoT for reasoning |
| **Claude** | XML tags, system prompt separation |
| **GPT** | Delimiters, structured output |

## Common Patterns

### Question Decomposition
```
Break down: How to build a web app?
1. Choose framework (Flask/FastAPI)
2. Design API endpoints
3. Implement routes
4. Add database
5. Deploy
```

### Self-Consistency
```
Solve this problem 3 ways:
Method 1: ...
Method 2: ...
Method 3: ...
Most consistent answer: ...
```

### Tree of Thoughts
```
Explore multiple reasoning paths:
Path A: ... (evaluation: 7/10)
Path B: ... (evaluation: 9/10) ← Choose this
```

## Prompt Optimization

### Reduce Token Usage
- Remove redundant instructions
- Use concise language
- Cache system prompt (if model supports)
- Compress examples (keep 2-3, not 10)

### Improve Accuracy
- Add constraints explicitly
- Use few-shot examples
- Ask for step-by-step reasoning
- Request结构化输出

### Testing Prompts
```python
test_cases = [
    ("What is 2+2?", "4"),
    ("Translate 'hello'", "Bonjour")
]
for question, expected in test_cases:
    response = llm.chat(question)
    assert expected in response
```

## Anti-Patterns to Avoid
- **Vague instructions**: "Do the thing" → Be specific
- **Overloading context**: Too much irrelevant info
- **Contradictory instructions**: "Be verbose. Be concise."
- **Missing output format**: Always specify expected format
- **No examples**: Add 2-3 examples for complex tasks

## Output Formats

### JSON (Structured)
```json
{
  "summary": "...",
  "key_points": ["...", "..."],
  "sentiment": "positive"
}
```

### Markdown (Readable)
```markdown
## Summary
...

## Key Points
- Point 1
- Point 2
```

### XML (LLM-Friendly)
```xml
<response>
  <summary>...</summary>
  <points>
    <point>1</point>
  </points>
</response>
```

## Guidelines
- Test prompts with multiple inputs
- Iterate based on outputs
- Keep system prompt <500 tokens
- Use few-shot for complex tasks
- Always specify output format
