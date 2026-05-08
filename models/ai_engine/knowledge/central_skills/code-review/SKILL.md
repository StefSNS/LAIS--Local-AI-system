---
name: code-review
description: Review code for security vulnerabilities, bugs, performance issues, and best practices. Use when user asks to review, critique, or analyze code.
---

# Code Review Skill

When activated, perform a thorough code review:

## Review Process

1. **Read the code files** to be reviewed
2. **Check for issues** in these categories:
   - Security vulnerabilities (SQL injection, XSS, hardcoded secrets, etc.)
   - Bugs and logic errors
   - Performance issues
   - Code smells and anti-patterns
   - Best practices violations
   - Error handling gaps
3. **Provide feedback** with severity levels (critical/high/medium/low)

## Output Format

```
## Issues Found

### Critical
- [File:line] Description and fix

### High
- [File:line] Description and fix

### Medium
- [File:line] Description and fix

### Low
- [File:line] Description and fix

## Recommendations
- Suggested improvements
- Code snippets for fixes
```

## Python-Specific Checks
- **Imports**: Unused, circular, or non-standard imports
- **Exceptions**: Bare `except:` clauses, missing specific exception types
- **Mutable defaults**: `def foo(x=[])` antipattern
- **F-strings**: Prefer over `.format()` or `%` in modern Python
- **Type hints**: Check for missing type annotations in function signatures
- **List/dict comprehensions**: Prefer over loops with `.append()`
- **Context managers**: Ensure `with` used for file I/O, locks, connections

## Code Review Pyramid (Priority Order)
1. **Structure** - Correct indentation, scope, module organization
2. **Logic** - Correct algorithm, edge cases, off-by-one errors
3. **Readability** - Naming, comments, function length (<50 lines)
4. **Conventions** - PEP 8 compliance, naming (snake_case, PascalCase)
5. **Performance** - O(n²) → O(n), unnecessary copies, lazy evaluation
6. **Style** - Formatting, whitespace, line length

## Security Checklist
- [ ] SQL injection (f-strings in queries)
- [ ] XSS vectors (unescaped user input)
- [ ] Hardcoded secrets (API keys, passwords)
- [ ] `eval()` / `exec()` usage
- [ ] Missing input validation
- [ ] Insecure deserialization (pickle)
- [ ] Command injection (os.system, subprocess with shell=True)

## Guidelines
- Be constructive, not harsh
- Explain WHY something is an issue
- Provide concrete fix suggestions
- Flag any security issues prominently
- Reference PEP 8 and Python anti-patterns