---
name: test-generator
description: Generate unit tests, integration tests, or test stubs. Use when user asks to create tests, write tests, or add test coverage.
---

# Test Generator Skill

## When to Use

- User asks to "write tests", "create tests", "add tests"
- User asks to "test this function/class"
- User provides a new file and asks for test coverage

## Test Generation Process

1. **Identify the module/file** to test
2. **Analyze the code** to understand:
   - Public functions/methods
   - Input parameters and types
   - Return values and expected behavior
   - Edge cases
3. **Generate appropriate tests**:
   - Use existing test framework in the project (pytest, unittest, etc.)
   - Match existing test style
   - Include both happy path and edge cases

## Output Format

```python
# test_module.py
import pytest
from module import function

class TestFunction:
    def test_happy_path(self):
        """Test normal operation"""
        result = function("input")
        assert result == expected

    def test_edge_case(self):
        """Test edge case"""
        with pytest.raises(Exception):
            function(invalid_input)
```

## Guidelines

- Name test files as `test_<module>.py`
- Use descriptive test names
- Include docstrings
- Test both success and failure cases
- Mock external dependencies if needed