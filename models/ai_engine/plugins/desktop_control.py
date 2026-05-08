import os, sys, json, shutil, subprocess, ctypes, tempfile, pyautogui
from pathlib import Path
from datetime import datetime

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

def _get_api_key():
    sys.path.insert(0, str(BASE_DIR))
    from utils.api_keys import get_gemini_api_key
    return get_gemini_api_key()

def _get_desktop():
    return Path.home() / "Desktop"

BLOCKED_KEYWORDS = [
    "os.remove", "shutil.rmtree", "subprocess.run", "subprocess.Popen",
    "os.system", "exec(", "eval(", "import os", "__import__", "open(",
]

def _is_safe_code(code):
    code_lower = code.lower()
    for keyword in BLOCKED_KEYWORDS:
        if keyword.lower() in code_lower:
            return False, f"Blocked: '{keyword}'"
    return True, "OK"

def _ask_gemini_for_desktop_action(task):
    import google.generativeai as genai
    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel("gemini-2.5-flash")
    desktop = str(_get_desktop())
    prompt = f"""Generate safe Python code using ONLY: pyautogui, Path, shutil, ctypes, time.
Desktop: {desktop}
Rules: NO file deletion, NO subprocess, NO exec/eval, output ONLY code, no markdown.
If unsafe, output: UNSAFE
Task: {task}
Python code:"""
    try:
        response = model.generate_content(prompt)
        code = response.text.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1]).strip()
        return code
    except Exception as e:
        return f"ERROR: {e}"

def _execute_generated_code(code):
    safe, reason = _is_safe_code(code)
    if not safe:
        return f"Blocked: {reason}"
    allowed_globals = {
        "pyautogui": pyautogui, "Path": Path, "shutil": shutil, "ctypes": ctypes,
        "time": __import__("time"), "os": type("os", (), {"path": os.path, "listdir": os.listdir})(),
        "__builtins__": {"print": print, "len": len, "str": str, "int": int, "float": float,
            "bool": bool, "list": list, "dict": dict, "range": range, "isinstance": isinstance}
    }
    output_lines = []
    allowed_globals["print"] = lambda *args: output_lines.append(" ".join(str(a) for a in args))
    try:
        exec(code, allowed_globals)
        return "\n".join(output_lines) if output_lines else "Task completed"
    except Exception as e:
        return f"Execution error: {e}"

def set_wallpaper(image_path):
    path = Path(image_path).expanduser().resolve()
    if not path.exists():
        return f"Image not found: {image_path}"
    if path.suffix.lower() not in [".jpg", ".jpeg", ".png", ".bmp"]:
        return f"Unsupported format: {path.suffix}"
    try:
        if sys.platform == "win32":
            ctypes.windll.user32.SystemParametersInfoW(20, 0, str(path.resolve()), 3)
            return f"Wallpaper set: {path.name}"
        elif sys.platform == "darwin":
            script = f'tell application "Finder" to set desktop picture to POSIX file "{path}"'
            subprocess.run(["osascript", "-e", script])
            return f"Wallpaper set: {path.name}"
        else:
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background",
                "picture-uri", f"file://{path}"])
            return f"Wallpaper set: {path.name}"
    except Exception as e:
        return f"Could not set wallpaper: {e}"

def set_wallpaper_from_web(url):
    try:
        import urllib.request
        suffix = Path(url.split("?")[0]).suffix or ".jpg"
        tmp = Path(tempfile.mktemp(suffix=suffix))
        urllib.request.urlretrieve(url, str(tmp))
        return set_wallpaper(str(tmp))
    except Exception as e:
        return f"Could not download wallpaper: {e}"

def get_current_wallpaper():
    try:
        if sys.platform == "win32":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop")
            val, _ = winreg.QueryValueEx(key, "Wallpaper")
            return f"Current wallpaper: {val}"
        return "Not supported on this OS"
    except Exception as e:
        return f"Could not get wallpaper: {e}"

FILE_TYPE_MAP = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".heic"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".csv", ".odt"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    "Music": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Code": [".py", ".js", ".html", ".css", ".json", ".xml", ".cpp", ".java"],
    "Executables": [".exe", ".msi", ".bat", ".cmd", ".sh"],
}

def organize_desktop(mode="by_type"):
    desktop = _get_desktop()
    moved, skipped = [], []
    for item in desktop.iterdir():
        if item.is_dir() or item.name.startswith(".") or item.suffix.lower() == ".lnk":
            continue
        if mode == "by_date":
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            folder_name = mtime.strftime("%Y-%m")
        else:
            ext = item.suffix.lower()
            folder_name = "Others"
            for folder, exts in FILE_TYPE_MAP.items():
                if ext in exts:
                    folder_name = folder; break
        target_dir = desktop / folder_name
        target_dir.mkdir(exist_ok=True)
        new_path = target_dir / item.name
        if new_path.exists():
            skipped.append(item.name); continue
        shutil.move(str(item), str(new_path))
        moved.append(f"{item.name} → {folder_name}/")
    result = f"Desktop organized ({mode}). {len(moved)} files moved."
    if moved:
        result += "\n" + "\n".join(moved[:8])
        if len(moved) > 8:
            result += f"\n... and {len(moved)-8} more."
    if skipped:
        result += f"\n{len(skipped)} files skipped (name conflict)."
    return result

def list_desktop():
    desktop = _get_desktop()
    items = []
    for item in sorted(desktop.iterdir()):
        if item.name.startswith("."): continue
        if item.is_dir():
            count = len(list(item.iterdir()))
            items.append(f"📁 {item.name}/ ({count} items)")
        else:
            size = item.stat().st_size
            size_str = f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/1024/1024:.1f} MB"
            items.append(f"📄 {item.name} ({size_str})")
    return f"Desktop ({len(items)} items):\n" + "\n".join(items) if items else "Desktop is empty."

def clean_desktop():
    desktop = _get_desktop()
    today = datetime.now().strftime("%Y-%m-%d")
    archive_dir = desktop / f"Desktop Archive {today}"
    archive_dir.mkdir(exist_ok=True)
    moved = 0
    for item in desktop.iterdir():
        if item.is_dir() or item.name.startswith(".") or item.suffix.lower() == ".lnk":
            continue
        if not (archive_dir / item.name).exists():
            shutil.move(str(item), str(archive_dir / item.name))
            moved += 1
    return f"Desktop cleaned. {moved} files moved to '{archive_dir.name}'."

def get_desktop_stats():
    desktop = _get_desktop()
    files = [i for i in desktop.iterdir() if i.is_file()]
    folders = [i for i in desktop.iterdir() if i.is_dir()]
    total_size = sum(f.stat().st_size for f in files)
    size_str = f"{total_size/1024:.1f} KB" if total_size < 1024*1024 else f"{total_size/1024/1024:.1f} MB"
    return f"Desktop stats:\n  Files: {len(files)}\n  Folders: {len(folders)}\n  Total size: {size_str}"

def desktop_control(parameters):
    action = (parameters or {}).get("action", "").lower().strip()
    task = (parameters or {}).get("task", "").strip()
    result = "Unknown action"
    try:
        if action == "wallpaper":
            path = parameters.get("path", "")
            result = set_wallpaper(path) if path else "No image path"
        elif action == "wallpaper_url":
            url = parameters.get("url", "")
            result = set_wallpaper_from_web(url) if url else "No URL"
        elif action == "current_wallpaper":
            result = get_current_wallpaper()
        elif action == "organize":
            mode = parameters.get("mode", "by_type")
            result = organize_desktop(mode)
        elif action == "clean":
            result = clean_desktop()
        elif action == "list":
            result = list_desktop()
        elif action == "stats":
            result = get_desktop_stats()
        elif action == "task" or task:
            actual_task = task or parameters.get("description", "")
            if not actual_task:
                return "Describe what you want to do"
            code = _ask_gemini_for_desktop_action(actual_task)
            if code == "UNSAFE":
                result = "Cannot perform safely"
            elif code.startswith("ERROR:"):
                result = f"Could not generate: {code}"
            else:
                result = _execute_generated_code(code)
        else:
            full_task = task or action
            if full_task:
                code = _ask_gemini_for_desktop_action(full_task)
                result = _execute_generated_code(code) if code != "UNSAFE" else "Cannot do safely"
            else:
                result = "No action specified"
    except Exception as e:
        result = f"Desktop error: {e}"
    return result
