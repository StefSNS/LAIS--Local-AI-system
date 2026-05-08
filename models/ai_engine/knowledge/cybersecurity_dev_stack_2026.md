# Cybersecurity Development Stack 2026

## OWASP Top 10 (2026)

1. **Broken Access Control** — Users can act outside intended permissions. Fix: deny by default, enforce RBAC/ABAC, rate limit.
2. **Cryptographic Failures** — Sensitive data exposed due to weak crypto. Fix: TLS everywhere, encrypt at rest, use Argon2/bcrypt.
3. **Injection** — SQL, NoSQL, OS, LDAP injection. Fix: parameterized queries, input validation, ORM with safe defaults.
4. **Insecure Design** — Missing security controls in architecture. Fix: threat modeling, secure design patterns, security reviews.
5. **Security Misconfiguration** — Default accounts, verbose errors, open ports. Fix: hardening checklists, automated config audits.
6. **Vulnerable/Outdated Components** — Unpatched dependencies. Fix: SBOM, dependency scanning, automated updates.
7. **Authentication Failures** — Weak passwords, session fixation, credential stuffing. Fix: MFA, passwordless auth, session management.
8. **Software/Data Integrity Failures** — Insecure CI/CD, unsigned updates. Fix: code signing, integrity checks, supply chain security.
9. **Security Logging/Monitoring Failures** — Undetected breaches. Fix: structured logging, SIEM integration, alerting thresholds.
10. **Server-Side Request Forgery (SSRF)** — Server makes unintended requests. Fix: allowlist domains, disable redirects, validate URLs.

---

## Secure Coding Practices

### Input Validation
- Validate on server-side, never trust client
- Use allowlists over blocklists
- Type-check all inputs (Pydantic, Zod, Joi)
- Sanitize output (XSS prevention)
- Max length limits on all fields

### Authentication & Authorization
- MFA for all sensitive operations
- JWT: short expiry + refresh tokens
- Password: Argon2id or bcrypt (min 10 rounds)
- Session: secure, httponly, samesame=strict cookies
- RBAC with principle of least privilege

### Encryption
- TLS 1.3 for all transit
- AES-256-GCM for data at rest
- Argon2id for password hashing
- Never store plaintext secrets — use vaults (HashiCorp, AWS Secrets Manager)
- Rotate keys regularly

### API Security
- Rate limiting (token bucket or sliding window)
- CORS: explicit origins, never `*` for sensitive endpoints
- API versioning to prevent breaking changes
- Input validation at API gateway level
- Pagination to prevent data exhaustion

### Logging & Monitoring
- Structured logging (JSON format)
- Never log sensitive data (passwords, tokens, PII)
- Correlation IDs for request tracing
- Alert on anomaly patterns (rate spikes, auth failures)
- Retention policy: 90 days minimum

---

## Pentesting Methodology

### 1. Reconnaissance
- **Passive**: WHOIS, DNS records, Shodan, Censys, GitHub dorking
- **Active**: Nmap, masscan, subdomain enumeration (Amass, Sublist3r)
- **OSINT**: theHarvester, Maltego, SpiderFoot

### 2. Scanning & Enumeration
- **Ports**: Nmap (`-sV -sC -O -p-`), RustScan
- **Web**: Nikto, Burp Suite, OWASP ZAP, ffuf/gobuster
- **Network**: enum4linux, smbmap, SNMPwalk
- **Cloud**: CloudMapper, ScoutSuite, Prowler

### 3. Exploitation
- **Web**: SQLi (sqlmap), XSS, SSRF, file inclusion, command injection
- **Network**: Metasploit, CrackMapExec, Impacket
- **Wireless**: Aircrack-ng, Reaver, Wifite
- **Password**: Hashcat, John the Ripper, Hydra

### 4. Post-Exploitation
- Privilege escalation (LinPEAS, WinPEAS)
- Lateral movement (Mimikatz, PsExec, WMI)
- Persistence (cron jobs, registry keys, scheduled tasks)
- Data exfiltration (encrypted channels, DNS tunneling)

### 5. Reporting
- Executive summary (risk-based, non-technical)
- Technical findings (CVSS scores, reproduction steps)
- Remediation recommendations (prioritized)
- Evidence (screenshots, logs, tool output)

---

## Pentesting Tool Stack

| Category | Tools |
|----------|-------|
| **Recon** | Nmap, Amass, Subfinder, theHarvester, Shodan |
| **Scanning** | Nikto, Nessus, OpenVAS, Burp Suite, OWASP ZAP |
| **Exploitation** | Metasploit, SQLmap, BeEF, Responder |
| **Password** | Hashcat, John, Hydra, CeWL, Crunch |
| **Post-Exploit** | Mimikatz, BloodHound, Empire, Covenant |
| **Wireless** | Aircrack-ng, Wifite, Reaver, Kismet |
| **Forensics** | Autopsy, Volatility, Wireshark, FTK |
| **Reporting** | Dradis, Faraday, Serpico |

---

## Vulnerability Databases & Resources

- **CVE**: https://cve.mitre.org
- **NVD**: https://nvd.nist.gov (National Vulnerability Database)
- **Exploit-DB**: https://www.exploit-db.com
- **OWASP Cheat Sheets**: https://cheatsheetseries.owasp.org
- **PayloadsAllTheThings**: https://github.com/swisskyrepo/PayloadsAllTheThings
- **HackTricks**: https://book.hacktricks.xyz
- **GTFOBins**: https://gtfobins.github.io (Linux priv esc)
- **LOLBAS**: https://lolbas-project.github.io (Windows living-off-the-land)

---

## Intentionally Vulnerable Practice Labs

- **DVWA** (Damn Vulnerable Web App): `docker pull citizenstig/dvwa`
- **OWASP Juice Shop**: `docker pull bkimminich/juice-shop`
- **WebGoat**: `docker pull webgoat/webgoat-8.0`
- **Metasploitable**: https://information.rapid7.com/metasploitable-download.html
- **HackTheBox**: https://www.hackthebox.com
- **TryHackMe**: https://tryhackme.com
