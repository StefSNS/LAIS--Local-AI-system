import time, subprocess, sys, platform, json
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

_OS = platform.system()

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

def volume_up():
    if _OS == "Windows":
        for _ in range(5): pyautogui.press("volumeup")
    elif _OS == "Darwin":
        subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) + 10)"])
    else:
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"])

def volume_down():
    if _OS == "Windows":
        for _ in range(5): pyautogui.press("volumedown")
    elif _OS == "Darwin":
        subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) - 10)"])
    else:
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"])

def volume_mute():
    if _OS == "Windows":
        pyautogui.press("volumemute")
    elif _OS == "Darwin":
        subprocess.run(["osascript", "-e", "set volume with output muted"])
    else:
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])

def volume_set(value: int):
    value = max(0, min(100, value))
    if _OS == "Windows":
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            import math
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            vol = cast(interface, POINTER(IAudioEndpointVolume))
            vol_db = -65.25 if value == 0 else max(-65.25, 20 * math.log10(value / 100))
            vol.SetMasterVolumeLevel(vol_db, None)
            return f"Volume set to {value}%"
        except Exception as e:
            return f"pycaw failed: {e}"
    elif _OS == "Darwin":
        subprocess.run(["osascript", "-e", f"set volume output volume {value}"])
        return f"Volume set to {value}%"
    else:
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{value}%"])
        return f"Volume set to {value}%"

def brightness_up():
    if _OS == "Windows":
        pyautogui.hotkey("win", "a"); time.sleep(0.3)
    elif _OS == "Darwin":
        subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 144'])
    else:
        subprocess.run(["brightnessctl", "set", "+10%"])

def brightness_down():
    if _OS == "Windows":
        pyautogui.hotkey("win", "a"); time.sleep(0.3)
    elif _OS == "Darwin":
        subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 145'])
    else:
        subprocess.run(["brightnessctl", "set", "10%-"])

def close_app():
    if _OS == "Darwin":
        pyautogui.hotkey("command", "q")
    else:
        pyautogui.hotkey("alt", "f4")

def close_window():
    if _OS == "Darwin":
        pyautogui.hotkey("command", "w")
    else:
        pyautogui.hotkey("ctrl", "w")

def full_screen():
    if _OS == "Darwin":
        pyautogui.hotkey("ctrl", "command", "f")
    else:
        pyautogui.press("f11")

def minimize_window():
    if _OS == "Darwin":
        pyautogui.hotkey("command", "m")
    else:
        pyautogui.hotkey("win", "down")

def maximize_window():
    if _OS == "Darwin":
        subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "f" using {control down, command down}'])
    else:
        pyautogui.hotkey("win", "up")

def snap_left():
    if _OS == "Windows": pyautogui.hotkey("win", "left")

def snap_right():
    if _OS == "Windows": pyautogui.hotkey("win", "right")

def switch_window():
    if _OS == "Darwin":
        pyautogui.hotkey("command", "tab")
    else:
        pyautogui.hotkey("alt", "tab")

def show_desktop():
    if _OS == "Darwin":
        pyautogui.hotkey("fn", "f11")
    elif _OS == "Windows":
        pyautogui.hotkey("win", "d")
    else:
        pyautogui.hotkey("super", "d")

def open_task_manager():
    if _OS == "Windows":
        pyautogui.hotkey("ctrl", "shift", "esc")
    elif _OS == "Darwin":
        subprocess.Popen(["open", "-a", "Activity Monitor"])
    else:
        subprocess.Popen(["gnome-system-monitor"])

def focus_search():
    if _OS == "Darwin": pyautogui.hotkey("command", "l")
    else: pyautogui.hotkey("ctrl", "l")

def pause_video(): pyautogui.press("space")
def refresh_page():
    if _OS == "Darwin": pyautogui.hotkey("command", "r")
    else: pyautogui.press("f5")

def close_tab():
    if _OS == "Darwin": pyautogui.hotkey("command", "w")
    else: pyautogui.hotkey("ctrl", "w")

def new_tab():
    if _OS == "Darwin": pyautogui.hotkey("command", "t")
    else: pyautogui.hotkey("ctrl", "t")

def next_tab():
    if _OS == "Darwin": pyautogui.hotkey("command", "shift", "bracketright")
    else: pyautogui.hotkey("ctrl", "tab")

def prev_tab():
    if _OS == "Darwin": pyautogui.hotkey("command", "shift", "bracketleft")
    else: pyautogui.hotkey("ctrl", "shift", "tab")

def go_back():
    if _OS == "Darwin": pyautogui.hotkey("command", "left")
    else: pyautogui.hotkey("alt", "left")

def go_forward():
    if _OS == "Darwin": pyautogui.hotkey("command", "right")
    else: pyautogui.hotkey("alt", "right")

def zoom_in():
    if _OS == "Darwin": pyautogui.hotkey("command", "equal")
    else: pyautogui.hotkey("ctrl", "equal")

def zoom_out():
    if _OS == "Darwin": pyautogui.hotkey("command", "minus")
    else: pyautogui.hotkey("ctrl", "minus")

def zoom_reset():
    if _OS == "Darwin": pyautogui.hotkey("command", "0")
    else: pyautogui.hotkey("ctrl", "0")

def find_on_page():
    if _OS == "Darwin": pyautogui.hotkey("command", "f")
    else: pyautogui.hotkey("ctrl", "f")

def scroll_up(amount=500): pyautogui.scroll(amount)
def scroll_down(amount=500): pyautogui.scroll(-amount)
def scroll_top():
    if _OS != "Darwin": pyautogui.hotkey("ctrl", "home")
    else: pyautogui.hotkey("command", "up")
def scroll_bottom():
    if _OS != "Darwin": pyautogui.hotkey("ctrl", "end")
    else: pyautogui.hotkey("command", "down")
def page_up(): pyautogui.press("pageup")
def page_down(): pyautogui.press("pagedown")

def copy():
    if _OS == "Darwin": pyautogui.hotkey("command", "c")
    else: pyautogui.hotkey("ctrl", "c")

def paste():
    if _OS == "Darwin": pyautogui.hotkey("command", "v")
    else: pyautogui.hotkey("ctrl", "v")

def cut():
    if _OS == "Darwin": pyautogui.hotkey("command", "x")
    else: pyautogui.hotkey("ctrl", "x")

def undo():
    if _OS == "Darwin": pyautogui.hotkey("command", "z")
    else: pyautogui.hotkey("ctrl", "z")

def redo():
    if _OS == "Darwin": pyautogui.hotkey("command", "shift", "z")
    else: pyautogui.hotkey("ctrl", "y")

def select_all():
    if _OS == "Darwin": pyautogui.hotkey("command", "a")
    else: pyautogui.hotkey("ctrl", "a")

def save_file():
    if _OS == "Darwin": pyautogui.hotkey("command", "s")
    else: pyautogui.hotkey("ctrl", "s")

def press_enter(): pyautogui.press("enter")
def press_escape(): pyautogui.press("escape")
def press_key(key): pyautogui.press(key)

def type_text(text, press_enter_after=False):
    if not text: return "No text provided"
    if _PYPERCLIP:
        pyperclip.copy(text); time.sleep(0.1); paste()
    else:
        pyautogui.write(str(text), interval=0.03)
    if press_enter_after:
        time.sleep(0.1); pyautogui.press("enter")
    return f"Typed: {text[:60]}"

def take_screenshot():
    if _OS == "Windows":
        pyautogui.hotkey("win", "shift", "s")
    elif _OS == "Darwin":
        pyautogui.hotkey("command", "shift", "3")
    else:
        pyautogui.hotkey("ctrl", "print_screen")
    return "Screenshot taken"

def lock_screen():
    if _OS == "Windows":
        pyautogui.hotkey("win", "l")
    elif _OS == "Darwin":
        subprocess.run(["pmset", "displaysleepnow"])
    else:
        subprocess.run(["gnome-screensaver-command", "-l"])
    return "Screen locked"

def open_system_settings():
    if _OS == "Windows":
        pyautogui.hotkey("win", "i")
    elif _OS == "Darwin":
        subprocess.Popen(["open", "-a", "System Preferences"])
    else:
        subprocess.Popen(["gnome-control-center"])
    return "System settings opened"

def open_file_explorer():
    if _OS == "Windows":
        pyautogui.hotkey("win", "e")
    elif _OS == "Darwin":
        subprocess.Popen(["open", Path.home()])
    else:
        subprocess.Popen(["xdg-open", Path.home()])
    return "File explorer opened"

def sleep_display():
    if _OS == "Windows":
        try:
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
        except: pass
    elif _OS == "Darwin":
        subprocess.run(["pmset", "displaysleepnow"])
    else:
        subprocess.run(["xset", "dpms", "force", "off"])
    return "Display sleeping"

def restart_computer():
    if _OS == "Windows":
        subprocess.run(["shutdown", "/r", "/t", "5"])
    elif _OS == "Darwin":
        subprocess.run(["osascript", "-e", 'tell application "System Events" to restart'])
    else:
        subprocess.run(["sudo", "reboot"])
    return "Restarting computer..."

def shutdown_computer():
    if _OS == "Windows":
        subprocess.run(["shutdown", "/s", "/t", "5"])
    elif _OS == "Darwin":
        subprocess.run(["osascript", "-e", 'tell application "System Events" to shut down'])
    else:
        subprocess.run(["sudo", "shutdown", "-h", "now"])
    return "Shutting down..."

def dark_mode():
    if _OS == "Windows":
        pyautogui.hotkey("win", "a"); time.sleep(0.3)
    elif _OS == "Darwin":
        subprocess.run(["osascript", "-e", 'tell app "System Events" to tell appearance preferences to set dark mode to not dark mode'])
    return "Dark mode toggled"

def toggle_wifi():
    if _OS == "Windows":
        pyautogui.hotkey("win", "a"); time.sleep(0.3)
    elif _OS == "Darwin":
        subprocess.run(["networksetup", "-setairportpower", "en0", "toggle"])
    else:
        subprocess.run(["nmcli", "radio", "wifi"])
    return "WiFi toggled"

ACTION_MAP = {
    "volume_up": volume_up, "volume_down": volume_down, "mute": volume_mute,
    "unmute": volume_mute, "brightness_up": brightness_up, "brightness_down": brightness_down,
    "pause_video": pause_video, "play_video": pause_video, "close_app": close_app,
    "close_window": close_window, "full_screen": full_screen, "minimize": minimize_window,
    "maximize": maximize_window, "snap_left": snap_left, "snap_right": snap_right,
    "switch_window": switch_window, "show_desktop": show_desktop, "screenshot": take_screenshot,
    "lock_screen": lock_screen, "open_settings": open_system_settings,
    "file_explorer": open_file_explorer, "restart": restart_computer, "shutdown": shutdown_computer,
    "dark_mode": dark_mode, "toggle_wifi": toggle_wifi, "refresh_page": refresh_page,
    "close_tab": close_tab, "new_tab": new_tab, "next_tab": next_tab, "prev_tab": prev_tab,
    "go_back": go_back, "go_forward": go_forward, "zoom_in": zoom_in, "zoom_out": zoom_out,
    "zoom_reset": zoom_reset, "find_on_page": find_on_page, "scroll_up": scroll_up,
    "scroll_down": scroll_down, "scroll_top": scroll_top, "scroll_bottom": scroll_bottom,
    "copy": copy, "paste": paste, "cut": cut, "undo": undo, "redo": redo,
    "select_all": select_all, "save": save_file, "enter": press_enter, "escape": press_escape,
}

def _detect_action(description):
    import google.generativeai as genai
    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    available = ", ".join(sorted(ACTION_MAP.keys())) + ", volume_set, type_text, press_key"
    prompt = f"""User said: "{description}"
Available actions: {available}
Return ONLY JSON: {{"action": "action_name", "value": null_or_value}}
Examples: "set volume to 60" → {{"action": "volume_set", "value": 60}}
Return ONLY the JSON object, no explanation."""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        import re
        text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
        return json.loads(text)
    except Exception as e:
        return {"action": description.lower().replace(" ", "_"), "value": None}

def computer_settings(parameters):
    if not _PYAUTOGUI:
        return "pyautogui not installed. Run: pip install pyautogui"
    params = parameters or {}
    raw_action = params.get("action", "").strip()
    description = params.get("description", "").strip()
    value = params.get("value", None)
    if not raw_action and description:
        detected = _detect_action(description)
        raw_action = detected.get("action", "")
        if value is None:
            value = detected.get("value")
    action = raw_action.lower().strip().replace(" ", "_").replace("-", "_")
    if not action:
        return "No action specified"
    if action == "volume_set":
        try:
            volume_set(int(value or 50))
            return f"Volume set to {value}%"
        except Exception as e:
            return f"Could not set volume: {e}"
    if action in ("type_text", "write_on_screen", "type", "write"):
        text = str(value or params.get("text", ""))
        if not text: return "No text provided"
        enter_after = bool(params.get("press_enter", False))
        type_text(text, press_enter_after=enter_after)
        return f"Typed: {text[:60]}"
    if action == "press_key":
        key = str(value or params.get("key", ""))
        if not key: return "No key specified"
        press_key(key)
        return f"Pressed: {key}"
    if action in ("scroll_up", "scroll_down"):
        try:
            amount = int(value or 500)
            scroll_up(amount) if action == "scroll_up" else scroll_down(amount)
            return f"Scrolled {'up' if action == 'scroll_up' else 'down'}"
        except Exception as e:
            return f"Scroll failed: {e}"
    func = ACTION_MAP.get(action)
    if not func:
        return f"Unknown action: {raw_action}"
    try:
        func()
        return f"Done: {action}"
    except Exception as e:
        return f"Action failed ({action}): {e}"
