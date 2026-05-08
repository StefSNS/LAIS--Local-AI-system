---
name: security-audit
description: Scan for security vulnerabilities, hardcoded secrets, and unsafe patterns. Use when user asks for security scan, security check, or mentions passwords/keys/secrets.
---

# Security Audit Skill

## When to Use

- User asks to "check security", "scan for vulnerabilities"
- User mentions passwords, keys, secrets, tokens
- User asks to "audit security"
- Working with authentication, encryption, or sensitive data

## Security Check Process

1. **Scan for common vulnerabilities**:
   - Hardcoded passwords/keys/secrets
   - SQL injection vectors
   - XSS vulnerabilities
   - Command injection
   - Insecure dependencies

2. **Check for unsafe patterns**:
   - `eval()`, `exec()` usage
   - Weak cryptographic algorithms
   - Missing input validation
   - Insecure file operations

3. **Report findings** with severity level

## Output Format

```
## Security Issues

### Critical
- [File:line] Issue: [description]
- Fix: [how to resolve]

### High
- [File:line] Issue: [description]
- Fix: [how to resolve]

## Recommendations
- Security best practices to follow
```

## Guidelines

- Take security issues seriously
- Always verify before claiming vulnerabilities
- Provide concrete remediation steps
- Suggest tools like bandit, semgrep for automation