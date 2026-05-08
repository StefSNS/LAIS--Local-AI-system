---
name: debug-assist
description: Debug errors, fix bugs, and trace issues. Use when user encounters errors, exceptions, bugs, or asks for help debugging.
---

# Debug Assist Skill

## When to Use

- User shows an error message or stack trace
- User says "it's not working", "getting an error"
- User asks to "debug this", "fix this bug"
- Code produces unexpected output

## Debugging Process

1. **Analyze the error**:
   - Read the full error message and stack trace
   - Identify the error type (SyntaxError, TypeError, ValueError, etc.)
   - Find the exact line where the error occurred

2. **Investigate the root cause**:
   - Read relevant code to understand the context
   - Check variable values at the error point
   - Trace back through the call stack if needed

3. **Propose fixes**:
   - Explain what's wrong and why
   - Provide corrected code
   - Suggest ways to prevent similar issues

## Python-Specific Debugging

### Common Error Types
| Error | Typical Cause | Fix |
|-------|---------------|-----|
| `NameError` | Variable not defined | Check scope, spelling |
| `TypeError` | Wrong type passed | Add type checks, isinstance() |
| `ValueError` | Correct type, wrong value | Validate input first |
| `KeyError` | Dict key missing | Use `.get()` with default |
| `IndexError` | List index out of range | Check len() before access |
| `AttributeError` | Method/attr doesn't exist | Check object type, imports |
| `ImportError` | Module not found | Check PYTHONPATH, install pkg |

### Debugging Tools
```python
# Insert debugging prints
print(f"DEBUG: variable = {variable}")

# Use pdb for interactive debugging
import pdb; pdb.set_trace()

# Check types
print(type(variable))
isinstance(variable, expected_type)
```

## Output Format

```
## Root Cause
[Explain what's wrong and why]

## Fix
```python
# Corrected code
```

## Prevention
[Suggestions to avoid similar issues]
```

## Guidelines

- Always read the actual error message first
- Ask user for full error details if not provided
- Don't assume - verify by reading the code
- Provide working code, not just explanations