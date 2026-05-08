---
name: documentation
description: Generate documentation, comments, or README files. Use when user asks to document, add docs, create README, or explain code.
---

# Documentation Skill

## When to Use

- User asks to "add documentation", "add comments"
- User asks to "create a README"
- User asks "what does this do" about code
- New code needs docstrings

## Documentation Process

1. **Understand the code**:
   - Read the relevant files
   - Identify public APIs and their purposes
   - Note dependencies and requirements

2. **Generate appropriate docs**:
   - For functions: docstrings with params, returns, raises
   - For classes: class docstring with usage examples
   - For modules: overview of what's provided
   - For projects: README with setup and usage

3. **Format correctly**:
   - Use the project's doc style (Google, NumPy, etc.)
   - Keep docstrings concise but complete
   - Include code examples where helpful

## Output Formats

### Docstring (function)
```python
def function(param1: str, param2: int) -> bool:
    """Short one-line description.

    Longer description if needed.

    Args:
        param1: Description of first param.
        param2: Description of second param.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param2 is invalid.
    """
```

### README
```markdown
# Project Name

Brief description.

## Installation

```bash
pip install project-name
```

## Usage

```python
from package import function

result = function("input")
```

## API Reference

### function(param1, param2)
Description...
```

## Guidelines

- Document the "why", not just the "what"
- Keep docstrings in sync with code
- Add examples for complex functions
- Use clear, simple language