import subprocess, sys, json, re
from pathlib import Path

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

def _get_api_key():
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]

def _get_platform():
    if sys.platform == "win32": return "windows"
    if sys.platform == "darwin": return "macos"
    return "linux"

WIN_COMMAND_MAP = [
    (["disk space", "disk usage", "storage"], "wmic logicaldisk get caption,freespace,size /format:list", False),
    (["running processes", "tasklist"], "tasklist /fo table", False),
    (["ip address", "ipconfig"], "ipconfig /all", False),
    (["ping", "internet"], "ping -n 4 google.com", False),
    (["open ports", "netstat"], "netstat -an | findstr LISTENING", False),
    (["wifi networks"], "netsh wlan show networks", False),
    (["system info", "specs"], "systeminfo", False),
    (["cpu usage"], "wmic cpu get loadpercentage", False),
    (["memory usage", "ram"], "wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value", False),
    (["installed programs"], "wmic product get name,version /format:table", False),
    (["battery"], 'powershell (Get-WmiObject -Class Win32_Battery).EstimatedChargeRemaining', False),
]

BLOCKED_PATTERNS = [
    r"\brm\s+-rf\b", r"\brmdir\s+/s\b", r"\bdel\s+/[fqs]",
    r"\bformat\b", r"\bdiskpart\b", r"\bshutdown\b", r"\brestart-computer\b",
    r"\bstop-process\b", r"\bkill\s+-9\b", r"\btaskkill\b",
]
_BLOCKED_RE = re.compile("|".join(BLOCKED_PATTERNS), re.IGNORECASE)

def _is_safe(command):
    match = _BLOCKED_RE.search(command)
    if match:
        return False, f"Blocked pattern: '{match.group()}'"
    return True, "OK"

def _find_hardcoded(task):
    task_lower = task.lower()
    if "notepad" in task_lower:
        file_match = re.search(r'[\"\']?([\S]+\.(?:txt|log|md|csv|json|xml))[\"\']?', task, re.IGNORECASE)
        if file_match:
            filename = file_match.group(1)
            desktop = Path.home() / "Desktop"
            filepath = Path(filename) if Path(filename).is_absolute() else desktop / filename
            return f'notepad "{filepath}"'
        return "notepad"
    pip_match = re.search(r"install\s+([\w\-]+)", task_lower)
    if pip_match:
        return f"pip install {pip_match.group(1)}"
    for keywords, command, _ in WIN_COMMAND_MAP:
        if any(kw in task_lower for kw in keywords):
            return command
    return None

def _ask_gemini(task):
    try:
        import google.generativeai as genai
        genai.configure(api_key=_get_api_key())
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        prompt = f"Convert to single Windows CMD command. Output ONLY command, no markdown.\nRequest: {task}\nCommand:"
        response = model.generate_content(prompt)
        command = response.text.strip().strip("`").strip()
        if command.startswith("```"):
            lines = command.split("\n")
            command = "\n".join(lines[1:-1]).strip()
        return command
    except Exception as e:
        return f"ERROR: {e}"

def _run_silent(command, timeout=20):
    try:
        platform = _get_platform()
        if platform == "windows":
            is_ps = command.strip().lower().startswith("powershell")
            if is_ps:
                cmd_inner = re.sub(r'^powershell\s+"?', '', command, flags=re.IGNORECASE).rstrip('"')
                result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd_inner],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
            else:
                result = subprocess.run(["cmd", "/c", command], capture_output=True, text=True,
                    encoding="cp1252", errors="replace", timeout=timeout, cwd=str(Path.home()))
        else:
            shell = "/bin/zsh" if platform == "macos" else "/bin/bash"
            result = subprocess.run(command, shell=True, executable=shell, capture_output=True,
                text=True, errors="replace", timeout=timeout, cwd=str(Path.home()))
        output = result.stdout.strip()
        error = result.stderr.strip()
        if output:
            try:
                from unified_layer.token_optimizer import get_token_optimizer
                output = get_token_optimizer("lais").compress_shell(output[:10000])
            except Exception:
                pass
            return output[:2000]
        if error: return f"[stderr]: {error[:500]}"
        return "Command executed with no output."
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s."
    except Exception as e:
        return f"Execution error: {e}"

def _run_visible(command):
    try:
        platform = _get_platform()
        if platform == "windows":
            subprocess.Popen(f'cmd /k "{command}"', creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif platform == "macos":
            subprocess.Popen(["osascript", "-e", f'tell application "Terminal" to do script "{command}"'])
        else:
            for term in ["gnome-terminal", "xterm", "konsole"]:
                try:
                    subprocess.Popen([term, "--", "bash", "-c", f"{command}; exec bash"])
                    break
                except FileNotFoundError:
                    continue
    except Exception as e:
        print(f"[CMD] Terminal open failed: {e}")

def cmd_control(parameters):
    task = (parameters or {}).get("task", "").strip()
    command = (parameters or {}).get("command", "").strip()
    visible = (parameters or {}).get("visible", True)
    if not task and not command:
        return "Please describe what you want to do"
    if not command:
        command = _find_hardcoded(task)
        if not command:
            print(f"[CMD] Asking Gemini: {task}")
            command = _ask_gemini(task)
            if command == "UNSAFE":
                return "Cannot generate safe command"
            if command.startswith("ERROR:"):
                return f"Could not generate command: {command}"
    safe, reason = _is_safe(command)
    if not safe:
        return f"Blocked: {reason}"
    if any(x in command.lower() for x in ["notepad", "explorer", "start "]):
        subprocess.Popen(command, shell=True)
        return f"Opened: {command}"
    if visible:
        _run_visible(command)
        output = _run_silent(command)
        return f"Terminal opened.\n\nOutput:\n{output}"
    return _run_silent(command)
