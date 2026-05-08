# Security Notice — LocalClaw / MARK XXXV

> **This document exists to demonstrate security awareness and responsible disclosure.**
> LocalClaw is a **local, personal AI assistant** intended for individual use on your own machine. The following information is provided so that users who deploy or modify this project can make informed decisions about their own security posture.

---

## Important Security Considerations

### 1. API Key Exposure (Critical)

This project requires a **Google Gemini API key** to function. By default, the key is stored in a `.env` file in the project root directory.

**Risks:**
- The `.env` file contains the key in **plaintext**
- There is **no `.gitignore`** — the `.env` could be accidentally committed
- Anyone with local access to your machine can read the key

**Recommended mitigations (user responsibility):**
- Add `.env` to a `.gitignore` file
- Use OS-level encryption (BitLocker, FileVault) on your drive
- Regularly rotate your API key via Google Cloud Console
- Set usage quotas and billing alerts on your Google Cloud project

### 2. Command Execution (High Risk)

The assistant can execute arbitrary commands via `cmd_control.py` and run generated code via `code_helper.py` and `dev_agent.py`. The AI model decides when to invoke these tools.

**Risks:**
- A malicious or hijacked AI session could execute harmful commands
- Generated Python code runs without sandboxing
- System files and settings can be modified

**Recommended mitigations (user responsibility):**
- Run the assistant in a limited user account (not Administrator)
- Use Windows Sandbox, a VM, or a dedicated machine for untrusted tasks
- Review code before execution when using `code_helper` / `dev_agent`
- Monitor active processes for unexpected behavior

### 3. File System Access (High Risk)

The assistant has full read/write access to your file system via `file_controller.py` and `desktop.py`.

**Risks:**
- Sensitive documents could be read, modified, or deleted
- Path traversal is theoretically possible if the AI misinterprets parameters

**Recommended mitigations (user responsibility):**
- Keep backups of important files (e.g., using Windows File History)
- Use folder permissions to restrict which directories the Python process can access
- Review file operations in the UI log panel

### 4. Browser Automation (Medium Risk)

The assistant controls Playwright-based browser automation via `browser_control.py`.

**Risks:**
- Could be directed to visit malicious websites
- Could be used to fill forms or submit data without user awareness
- Session cookies and saved passwords in the browser profile could be exposed

**Recommended mitigations (user responsibility):**
- Use a dedicated browser profile with no saved passwords
- Avoid being logged into sensitive accounts during testing
- Use the incognito mode parameter (`incognito: true`) for sensitive sessions

### 5. Memory/Privacy (Medium Risk)

User conversations, preferences, and personal facts are stored in `memory/long_term.json` in plaintext.

**Risks:**
- Sensitive personal data is stored unencrypted
- A local attacker could read all stored memories

**Recommended mitigations (user responsibility):**
- Encrypt the `memory/` directory or use an encrypted drive
- Periodically review and clear stored memories via the `save_memory` tool
- Do not share sensitive credentials (passwords, PINs) with the assistant

### 6. Dependency Supply Chain (Low Risk)

The project uses pip-installed packages listed in `requirements.txt` without a lockfile.

**Risks:**
- Transitive dependency updates could introduce malicious code
- No integrity verification of downloaded packages

**Recommended mitigations (user responsibility):**
- Pin all dependencies with version numbers
- Generate a `requirements.lock` file after testing
- Use `pip audit` or `safety` to scan for known vulnerabilities
- Review dependency changes before updating

### 7. Network Egress (Low Risk)

The assistant makes outbound HTTPS calls to Google Gemini APIs and web search services.

**Risks:**
- Data sent to Gemini (voice, text, screen captures) is processed on Google servers
- Web search queries go to external search engines

**Recommended mitigations (user responsibility):**
- Review Google's data handling policies for Gemini API
- Disable web search via the UI or configuration if not needed
- Use a firewall to restrict outbound connections if desired

---

## Quick Reference

| Risk Area | Severity | User Action Required |
|-----------|----------|---------------------|
| API key in `.env` | **Critical** | Add `.gitignore`, enable disk encryption, rotate key |
| Command execution | **High** | Run in limited account, use sandbox/VM |
| File system access | **High** | Keep backups, restrict directories |
| Browser automation | **Medium** | Use dedicated profile, avoid saved passwords |
| Memory storage | **Medium** | Encrypt memory directory, review periodically |
| Dependency supply chain | **Low** | Pin versions, scan vulnerabilities |
| Network egress | **Low** | Review API privacy policy, restrict if needed |

---

## Deployment Recommendations by Risk Level

### Basic (casual local use)
- Add `.env` to `.gitignore`
- Enable BitLocker or equivalent disk encryption
- Run as a standard (non-admin) user

### Enhanced (production or shared machine)
- All of Basic, plus:
- Run inside a Windows Sandbox or VM
- Use a dedicated limited Windows user account
- Pin all `requirements.txt` versions
- Generate and verify a `requirements.lock` file

### Maximum (security-sensitive environment)
- All of Enhanced, plus:
- Disable `cmd_control`, `code_helper`, and `dev_agent` if not needed
- Use a firewall to restrict outbound destinations
- Regularly audit `memory/long_term.json` contents
- Use separate Gemini API key with strict quota limits

---

## Reporting Security Issues

This project is open-source and community-maintained. If you discover a security-relevant issue:
1. Check if the issue is already documented above
2. Apply the recommended mitigations for your risk level
3. Report issues to the project repository

---

*Last updated: May 2026*
