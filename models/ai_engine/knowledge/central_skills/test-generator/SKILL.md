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

## Python Testing Best Practices (from roadmap.sh/Python)

### Test Types
| Type | Purpose | Framework |
|------|---------|------------|
| **Unit** | Test individual functions/classes | pytest, unittest |
| **Integration** | Test component interactions | pytest |
| **E2E** | Test full user flows | pytest + selenium |
| **Property-based** | Test invariants | hypothesis |

### pytest Patterns
```python
import pytest

# Parametrized tests
@pytest.mark.parametrize("input,expected", [
    ("hello", 5),
    ("world", 5),
])
def test_length(input, expected):
    assert len(input) == expected

# Fixtures for setup
@pytest.fixture
def db_connection():
    conn = create_connection()
    yield conn
    conn.close()

# Mocking
from unittest.mock import Mock, patch
@patch('module.ExternalAPI')
def test_with_mock(mock_api):
    mock_api.return_value = "mocked"
    result = function_under_test()
    assert result == "expected"
```

### What to Test
- **Happy path**: Normal inputs, expected outputs
- **Edge cases**: Empty lists, None, 0, negative numbers
- **Error cases**: Invalid input, exceptions raised
- **Boundary values**: Min/max values, off-by-one
- **Types**: Wrong types passed (if no type hints)

### Coverage Goals
- Aim for 80%+ coverage on business logic
- 100% on critical paths (auth, payments)
- Don't test trivial getters/setters

## Guidelines
- Name test files as `test_<module>.py`
- Use descriptive test names
- Include docstrings
- Test both success and failure cases
- Mock external dependencies if needed