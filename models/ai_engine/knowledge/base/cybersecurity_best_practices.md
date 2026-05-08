# Cybersecurity Best Practices

## Core Principles

### 1. Defense in Depth
Multiple layers of security - no single defense is foolproof.

### 2. Least Privilege
Grant minimum permissions needed to accomplish tasks.

### 3. Fail Securely
System should default to deny when errors occur.

### 4. Assume Breach
Act as if attackers already in - plan for incident response.

## Common Vulnerabilities

### OWASP Top 10 (Web)
1. **A01: Broken Access Control** - Users acting outside intended permissions
2. **A02: Cryptographic Failures** - Weak encryption, key management issues
3. **A03: Injection** - SQL, NoSQL, OS command injection
4. **A04: Insecure Design** - Missing security controls
5. **A05: Security Misconfiguration** - Unnecessary features enabled
6. **A06: Vulnerable Components** - Using outdated libraries
7. **A07: Auth Failures** - Weak passwords, session issues
8. **A08: Data Integrity Failures** - Not validating data
9. **A09: Logging Failures** - Not logging security events
10. **A10: SSRF** - Server-side request forgery

## Secure Coding Practices

### Authentication
- Use strong password policies (12+ chars, complexity)
- Never store plain text passwords - use bcrypt/argon2
- Implement MFA/2FA
- Session timeouts (15 min idle)
- Secure session cookies (HttpOnly, Secure, SameSite)

### Input Validation
- Validate on server (never trust client)
- Use parameterized queries (prevent SQLi)
- Sanitize file uploads
- Limit request sizes
- Use allowlists over denylists

### Encryption
- TLS 1.2+ for transit
- AES-256 for data at rest
- Don't roll your own crypto
- Proper key management
- Never hardcode secrets

### Dependencies
- Keep libraries updated
- Use tools like dependabot, snyk
- Review changes before updating
- Remove unused dependencies
- Pin versions in production

## Security Checklist

- [ ] Authentication properly implemented
- [ ] Passwords hashed with bcrypt/argon2
- [ ] HTTPS enforced everywhere
- [ ] Input validation on all inputs
- [ ] Parameterized queries used
- [ ] Dependencies up to date
- [ ] Security headers set
- [ ] Rate limiting on auth endpoints
- [ ] Logging of security events
- [ ] Regular security audits