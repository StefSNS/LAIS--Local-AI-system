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

## Guidelines

- Be constructive, not harsh
- Explain WHY something is an issue
- Provide concrete fix suggestions
- Flag any security issues prominently