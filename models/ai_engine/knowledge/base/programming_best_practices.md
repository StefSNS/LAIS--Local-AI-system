# Programming Best Practices

## General Principles

### Code Quality
- **DRY**: Don't Repeat Yourself
- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Aren't Gonna Need It
- **SOLID**: Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, Dependency Inversion

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Variables | snake_case | `user_name` |
| Constants | UPPER_SNAKE | `MAX_RETRY` |
| Functions | snake_case | `get_user()` |
| Classes | PascalCase | `UserService` |
| Files | snake_case | `user_service.py` |

### Comments

- **Why, not what**: Explain intent, not code
- **Keep updated**: Comments sync with code
- **Use docstrings**: For public APIs
- **Avoid obvious**: Don't comment obvious code

### Error Handling

- **Specific exceptions**: Catch specific, not broad
- **Log meaningful**: Include context
- **Fail gracefully**: User-friendly messages
- **Don't swallow**: Always handle or re-raise

## Python Specific

### Best Practices
- Use type hints
- Use f-strings for formatting
- Use list comprehensions over loops
- Use enumerate over range(len())
- Use f-strings for formatting
- Use dataclasses for simple objects

### Avoid
- `eval()` and `exec()`
- Wildcard imports: `from x import *`
- Mutable default arguments
- Checking type with `==` not `isinstance()`

## JavaScript Specific

### Best Practices
- Use const/let, avoid var
- Use arrow functions for callbacks
- Use template literals
- Use destructuring
- Use async/await over promises

### Avoid
- `==` (use `===`)
- var (use let/const)
- Callback hell (use async/await)
- Mutating state directly

## Version Control

- Commit often with meaningful messages
- Branch for features
- Code review before merge
- Don't commit secrets
- Use .gitignore properly