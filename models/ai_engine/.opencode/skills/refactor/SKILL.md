---
name: refactor
description: Refactor code for better structure, readability, or performance. Use when user asks to refactor, improve, or clean up code.
---

# Refactor Skill

## When to Use

- User asks to "refactor", "clean up", "improve"
- User asks to "make this more readable/efficient"
- Code is duplicated, too complex, or hard to maintain

## Refactoring Process

1. **Analyze the code**:
   - Understand what the code does
   - Identify issues (duplication, complexity, coupling)
   - Note the existing style and conventions

2. **Plan improvements**:
   - Extract repeated code into functions
   - Simplify complex conditions
   - Break large functions into smaller pieces
   - Rename for clarity
   - Add proper docstrings

3. **Apply changes**:
   - Make one logical change at a time
   - Preserve the original behavior
   - Update tests if needed

## Output Format

```
## Issues Found
- [Issue description]

## Refactored Code
```python
# New code here
```

## Changes Made
1. [Change 1]
2. [Change 2]
```

## Guidelines

- Don't change behavior, only structure
- Preserve variable/function names unless confusing
- Keep changes minimal and focused
- Match the project's code style