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

## Refactoring Patterns (from roadmap.sh/Python + System Design)

### Code Smells to Fix
| Smell | Refactoring |
|-------|-------------|
| Duplicated code | Extract function/method |
| Long function (>50 lines) | Extract smaller functions |
| Large class (>200 lines) | Split into modules |
| Long parameter list | Introduce parameter object |
| Feature envy (class uses another more than its own) | Move method |
| Switch statements (if/elif chains) | Polymorphism, dict dispatch |
| Mutable defaults (`def f(x=[])`) | Use `None` + initialize inside |
| Deep nesting (>3 levels) | Early returns, guard clauses |

### Pythonic Refactoring
```python
# Before: Not Pythonic
result = []
for i in range(len(items)):
    if items[i] > 0:
        result.append(items[i] * 2)

# After: List comprehension
result = [x * 2 for x in items if x > 0]

# Before: Mutable default
def add_item(item, lst=[]):
    lst.append(item)
    return lst

# After: None default
def add_item(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

### Performance Refactoring
- Replace string concat in loops with `join()`
- Use generators for large datasets (`yield`)
- Replace linear searches with `set`/`dict` lookups
- Use `__slots__` for memory-heavy objects
- Lazy import heavy modules if rarely used

## Guidelines
- Don't change behavior, only structure
- Preserve variable/function names unless confusing
- Keep changes minimal and focused
- Match the project's code style