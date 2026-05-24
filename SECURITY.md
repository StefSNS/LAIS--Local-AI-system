# LAIS Security Notice

> **LAIS is a local AI assistant with full system access.**
> Read this before deployment.

---

## Critical Risks

### 1. API Key Exposure (Critical)
Your Gemini API key is stored in `models/Mark-XXXIX/config/api_keys.json` in plaintext.

**Mitigations:**
- Add `config/api_keys.json` to `.gitignore`
- Enable disk encryption (BitLocker, FileVault)
- Set usage quotas on your Google Cloud project

### 2. Command Execution (High)
JARVIS can execute arbitrary commands and code via desktop control and code helpers.

**Mitigations:**
- Run in a limited user account (not Administrator)
- Use Windows Sandbox or a VM for untrusted tasks
- Review code before execution

### 3. File System Access (High)
The system has full read/write access to your files.

**Mitigations:**
- Keep backups of important files
- Use folder permissions to restrict access
- Review file operations in the UI

### 4. Browser Automation (Medium)
Playwright-based browser control can visit websites and fill forms.

**Mitigations:**
- Use a dedicated browser profile
- Avoid being logged into sensitive accounts
- Use incognito mode for sensitive sessions

### 5. Network Egress (Low)
The assistant makes outbound calls to Google Gemini APIs and web search.

**Mitigations:**
- Review Google's data handling policies
- Disable web search if not needed
- Use a firewall to restrict outbound connections

---

## Quick Reference

| Risk Area | Severity | Action Required |
|-----------|----------|----------------|
| API key in config | Critical | Add to .gitignore, enable encryption |
| Command execution | High | Run in limited account, use sandbox |
| File system access | High | Keep backups, restrict directories |
| Browser automation | Medium | Use dedicated profile |
| Network egress | Low | Review API privacy policy |

---

## Reporting Issues

Report security issues to the project repository.
