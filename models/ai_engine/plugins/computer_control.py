import json, sys, time, random, string, subprocess, platform
from pathlib import Path

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

def _load_user_profile():
    memory_path = BASE_DIR / "memory" / "long_term.json"
    try:
        if memory_path.exists():
            data = json.loads(memory_path.read_text(encoding="utf-8"))
            identity = data.get("identity", {})
            return {
                "name": identity.get("name", {}).get("value", ""),
                "email": identity.get("email", {}).get("value", ""),
            }
    except: pass
    return {}

def _ensure_pyautogui():
    if not _PYAUTOGUI:
        raise RuntimeError("PyAutoGUI not installed")

_FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Drew", "Quinn"]
_LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "proton.me"]

def generate_random_data(data_type):
    dt = data_type.lower().strip()
    if dt == "first_name": return random.choice(_FIRST_NAMES)
    if dt == "last_name": return random.choice(_LAST_NAMES)
    if dt == "name": return f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"
    if dt == "email":
        return f"{random.choice(_FIRST_NAMES).lower()}.{random.choice(_LAST_NAMES).lower()}{random.randint(10,999)}@{random.choice(_DOMAINS)}"
    if dt == "username": return f"{random.choice(_FIRST_NAMES).lower()}{random.randint(100,9999)}"
    if dt == "password":
        chars = string.ascii_letters + string.digits + "!@#$%"
        pwd = random.choice(string.ascii_uppercase) + random.choice(string.digits) + random.choice("!@#$%") + "".join(random.choices(chars, k=9))
        return "".join(random.sample(pwd, len(pwd)))
    if dt == "phone": return f"+1{random.randint(200,999)}{random.randint(1000000,9999999)}"
    if dt == "birthday": return f"{random.randint(1,12):02d}/{random.randint(1,28):02d}/{random.randint(1980,2000)}"
    if dt == "address": return f"{random.randint(100,9999)} {random.choice(['Main St', 'Oak Ave', 'Park Blvd', 'Elm St'])}"
    if dt == "zip_code": return str(random.randint(10000, 99999))
    return f"random_{data_type}_{random.randint(1000,9999)}"

def _type_text(text, interval=0.03):
    _ensure_pyautogui()
    time.sleep(0.3)
    pyautogui.typewrite(text, interval=interval)
    return f"Typed: {text[:50]}"

def _click(x=None, y=None, button="left", clicks=1, image=None):
    _ensure_pyautogui()
    if image:
        try:
            loc = pyautogui.locateCenterOnScreen(image, confidence=0.8)
            if loc:
                pyautogui.click(loc.x, loc.y, button=button, clicks=clicks)
                return f"Clicked image: {image}"
            return f"Image not found: {image}"
        except Exception as e:
            return f"Image click failed: {e}"
    if x is not None and y is not None:
        pyautogui.click(x, y, button=button, clicks=clicks)
        return f"Clicked ({x}, {y})"
    pyautogui.click(button=button, clicks=clicks)
    return "Clicked at current position"

def _hotkey(*keys):
    _ensure_pyautogui()
    pyautogui.hotkey(*keys)
    return f"Hotkey: {'+'.join(keys)}"

def _press(key):
    _ensure_pyautogui()
    pyautogui.press(key)
    return f"Pressed: {key}"

def _scroll(direction="down", amount=3):
    _ensure_pyautogui()
    clicks = amount if direction in ("up", "right") else -amount
    if direction in ("up", "down"):
        pyautogui.scroll(clicks)
    else:
        pyautogui.hscroll(clicks)
    return f"Scrolled {direction} {amount} times"

def _move_mouse(x, y, duration=0.3):
    _ensure_pyautogui()
    pyautogui.moveTo(x, y, duration=duration)
    return f"Mouse moved to ({x}, {y})"

def _drag(x1, y1, x2, y2, duration=0.5):
    _ensure_pyautogui()
    pyautogui.drag(x1 - pyautogui.position()[0], y1 - pyautogui.position()[1])
    pyautogui.dragTo(x2, y2, duration=duration)
    return f"Dragged from ({x1},{y1}) to ({x2},{y2})"

def _screenshot(save_path=None):
    _ensure_pyautogui()
    if not save_path:
        save_path = str(Path.home() / "Desktop" / "screenshot.png")
    pyautogui.screenshot().save(save_path)
    return f"Screenshot saved: {save_path}"

def _wait(seconds):
    time.sleep(seconds)
    return f"Waited {seconds}s"

def _wait_for_image(image_path, timeout=10):
    _ensure_pyautogui()
    start = time.time()
    while time.time() - start < timeout:
        try:
            loc = pyautogui.locateCenterOnScreen(image_path, confidence=0.8)
            if loc: return f"Image found at ({loc.x}, {loc.y})"
        except Exception as e:
            pass
        time.sleep(0.5)
    return f"Image not found within {timeout}s"

def _get_screen_size():
    _ensure_pyautogui()
    w, h = pyautogui.size()
    return f"{w}x{h}"

def _focus_window(title):
    if platform.system() == "Windows":
        try:
            script = f'(New-Object -ComObject WScript.Shell).AppActivate("{title}")'
            subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, timeout=5)
            time.sleep(0.3)
            return f"Focused window: {title}"
        except Exception as e:
            return f"Could not focus: {e}"
    return "Window focus only on Windows"

def _clear_field():
    _hotkey("ctrl", "a")
    time.sleep(0.1)
    _press("delete")
    return "Field cleared"

def _smart_type(text, clear_first=True):
    _ensure_pyautogui()
    if clear_first:
        _clear_field(); time.sleep(0.1)
    if len(text) > 20 and _PYPERCLIP:
        pyperclip.copy(text); time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
        return f"Smart-typed (clipboard): {text[:50]}"
    pyautogui.typewrite(text, interval=0.04)
    return f"Smart-typed: {text[:50]}"

def _analyze_screen_for_element(description):
    try:
        import google.generativeai as genai
        import io
        sys.path.insert(0, str(BASE_DIR))
        from utils.api_keys import get_gemini_api_key
        genai.configure(api_key=get_gemini_api_key())
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        _ensure_pyautogui()
        w, h = pyautogui.size()
        img = pyautogui.screenshot()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        prompt = f"Screenshot {w}x{h}. Find: '{description}'. Return ONLY x,y or NOT_FOUND"
        response = model.generate_content([{"mime_type": "image/png", "data": buf.getvalue()}, prompt])
        text = response.text.strip()
        if "NOT_FOUND" in text: return None
        match = re.search(r"(\d+)\s*,\s*(\d+)", text)
        if match: return int(match.group(1)), int(match.group(2))
    except Exception as e: pass
    return None

def computer_control(parameters):
    action = (parameters or {}).get("action", "").lower().strip()
    if not action:
        return "Specify an action"
    try:
        if action == "type":
            return _type_text(parameters.get("text", ""))
        elif action == "smart_type":
            return _smart_type(parameters.get("text", ""), parameters.get("clear_first", True))
        elif action in ("click", "left_click"):
            return _click(x=parameters.get("x"), y=parameters.get("y"), button="left", clicks=1, image=parameters.get("image"))
        elif action == "double_click":
            return _click(x=parameters.get("x"), y=parameters.get("y"), button="left", clicks=2, image=parameters.get("image"))
        elif action == "right_click":
            return _click(x=parameters.get("x"), y=parameters.get("y"), button="right", clicks=1)
        elif action == "move":
            return _move_mouse(x=int(parameters.get("x", 0)), y=int(parameters.get("y", 0)), duration=float(parameters.get("duration", 0.3)))
        elif action == "drag":
            return _drag(x1=int(parameters.get("x1", 0)), y1=int(parameters.get("y1", 0)), x2=int(parameters.get("x2", 0)), y2=int(parameters.get("y2", 0)))
        elif action == "hotkey":
            keys = parameters.get("keys", "")
            if isinstance(keys, str): keys = [k.strip() for k in keys.split("+")]
            return _hotkey(*keys)
        elif action == "press":
            return _press(parameters.get("key", "enter"))
        elif action == "scroll":
            return _scroll(direction=parameters.get("direction", "down"), amount=int(parameters.get("amount", 3)))
        elif action == "copy":
            if _PYPERCLIP: return pyperclip.paste()
            _hotkey("ctrl", "c"); time.sleep(0.2)
            return "Copied to clipboard"
        elif action == "paste":
            if _PYPERCLIP:
                pyperclip.copy(parameters.get("text", "")); time.sleep(0.1)
                _hotkey("ctrl", "v")
                return f"Pasted: {parameters.get('text', '')[:50]}"
            return "pyperclip not available"
        elif action == "screenshot":
            return _screenshot(parameters.get("path"))
        elif action == "wait":
            return _wait(float(parameters.get("seconds", 1.0)))
        elif action == "wait_image":
            return _wait_for_image(parameters.get("image", ""), timeout=int(parameters.get("timeout", 10)))
        elif action == "clear_field":
            return _clear_field()
        elif action == "focus_window":
            return _focus_window(parameters.get("title", ""))
        elif action == "screen_size":
            return _get_screen_size()
        elif action == "screen_find":
            description = parameters.get("description", "")
            coords = _analyze_screen_for_element(description)
            return f"{coords[0]},{coords[1]}" if coords else "NOT_FOUND"
        elif action == "screen_click":
            description = parameters.get("description", "")
            coords = _analyze_screen_for_element(description)
            if coords:
                time.sleep(0.2)
                _click(x=coords[0], y=coords[1])
                return f"Clicked: {description} at {coords}"
            return f"Not found: {description}"
        elif action == "random_data":
            return generate_random_data(parameters.get("type", "name"))
        elif action == "user_data":
            field = parameters.get("field", "name")
            profile = _load_user_profile()
            value = profile.get(field, "")
            if not value:
                value = generate_random_data(field)
            return value
        else:
            return f"Unknown action: {action}"
    except Exception as e:
        return f"Failed: {e}"
