# How to Combat Top 15 Hacker Methods

## Attack Vectors & Defenses

### 1. SQL Injection
**Attack**: Malicious SQL in user input
```
' OR '1'='1' --
```
**Defense**:
- Use parameterized queries
- Input validation
- Least privilege DB user
- Use ORM

### 2. Cross-Site Scripting (XSS)
**Attack**: Inject malicious JavaScript
```
<script>stealCookie()</script>
```
**Defense**:
- Escape output (OWASP ESAPI)
- Content Security Policy
- HttpOnly cookies
- Output encoding

### 3. Cross-Site Request Forgery (CSRF)
**Attack**: Trick user into submitting malicious request
**Defense**:
- CSRF tokens
- SameSite cookies
- Check Origin header
- Custom header requirement

### 4. Password Attacks
**Attack**: Brute force, dictionary, spray
**Defense**:
- Rate limiting
- Account lockout
- Strong hashing (bcrypt, argon2)
- MFA
- Password blocklists

### 5. Man-in-the-Middle (MITM)
**Attack**: Intercept traffic between user/server
**Defense**:
- TLS everywhere
- Certificate pinning
- HSTS header
- Verify certificates

### 6. DDoS Attacks
**Attack**: Flood with traffic
**Defense**:
- Rate limiting
- CDN (Cloudflare, etc.)
- Load balancing
- Traffic scrubbing
- Auto-scaling

### 7. Zero-Day Exploits
**Attack**: Unknown vulnerabilities
**Defense**:
- Keep software updated
- WAF rules
- Minimize attack surface
- Intrusion detection
- Vulnerability scanning

### 8. Social Engineering/Phishing
**Attack**: Trick users into revealing info
**Defense**:
- User training
- Email filtering
- SPF/DKIM/DMARC
- Verify requests
- Multi-factor auth

### 9. Credential Stuffing
**Attack**: Use leaked credentials elsewhere
**Defense**:
- Unique passwords per site
- Password manager
- HaveIBeenPwned check
- MFA everywhere
- Device fingerprinting

### 10. Remote Code Execution (RCE)
**Attack**: Execute arbitrary code on server
**Defense**:
- Don't use eval/exec
- Container isolation
- Least privilege
- Input validation
- Patch immediately

### 11. Directory Traversal
**Attack**: Access files outside web root
```
../../../etc/passwd
```
**Defense**:
- Validate paths
- Chroot jail
- File permission limits
- Use safe path functions

### 12. XML External Entity (XXE)
**Attack**: Inject malicious XML
```xml
<!ENTITY xxe SYSTEM "file:///etc/passwd">
```
**Defense**:
- Disable XML external entities
- Use JSON when possible
- Validate XML
- Disable DTD

### 13. Insecure Deserialization
**Attack**: Malicious serialized object
**Defense**:
- Don't deserialize untrusted data
- Use JSON overpickle
- Integrity checks
- Type checks

### 14. Server-Side Request Forgery (SSRF)
**Attack**: Make server request internal resources
```
http://169.254.169.254/latest/meta-data/
```
**Defense**:
- Validate URLs
- Deny internal access
- Use allowlists
- Disable redirect following

### 15. Supply Chain Attacks
**Attack**: Compromise dependencies
**Defense**:
- Pin versions
- Use lock files
- Scan dependencies
- Minimal dependencies
- Subresource integrity

## Quick Reference

| Attack | Key Defense |
|--------|-------------|
| SQLi | Parameterized queries |
| XSS | Escape output |
| CSRF | Tokens |
| Password | MFA |
| MITM | TLS |
| DDoS | CDN/rate limiting |
| Zero-day | Update fast |
| Phishing | Training+MFA |
| RCE | Least privilege |
| XXE | Disable entities |