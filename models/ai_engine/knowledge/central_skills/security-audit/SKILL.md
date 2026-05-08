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

## OWASP API Security Top 10 (from roadmap.sh)

1. **Broken Object Level Auth** - Check user can only access own resources
2. **Broken Authentication** - MFA, strong password policy, session mgmt
3. **Excessive Data Exposure** - Return only required fields
4. **Lack of Resource & Rate Limiting** - Implement throttling
5. **Broken Function Level Auth** - Check admin vs regular user perms
6. **Mass Assignment** - Whitelist allowed input fields
7. **Security Misconfiguration** - Disable debug, default creds
8. **Injection** - Parameterized queries, input validation
9. **Improper Assets Management** - Document all endpoints/versions
10. **Insufficient Logging** - Log auth failures, 4xx, 5xx

## Python Security Checks
- **Hardcoded secrets**: `password = "secret"`, API keys in code
- **`eval()` / `exec()`**: Arbitrary code execution risk
- **`pickle` deserialization**: Insecure, use JSON instead
- **`os.system()` / `subprocess` with `shell=True`**: Command injection
- **SQL queries with f-strings**: Use parameterized queries
- **`random` module**: Not cryptographically secure, use `secrets`
- **Missing `@login_required`**: Unprotected endpoints
- **Debug=True in prod**: Information leakage

## Tools to Suggest
- **bandit**: Static security linting for Python
- **semgrep**: Pattern-based security scanning
- **safety**: Check dependencies for known CVEs
- **OWASP ZAP**: Dynamic API security testing

## Guidelines
- Take security issues seriously
- Always verify before claiming vulnerabilities
- Provide concrete remediation steps
- Suggest tools like bandit, semgrep for automation