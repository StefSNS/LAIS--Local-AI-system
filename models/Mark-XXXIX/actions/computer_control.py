"""Computer control action."""

def computer_control(parameters, player):
    action = parameters.get("action", "")
    value = parameters.get("value", "")

    if player:
        player.ui.write_log(f"Computer: {action}")

    if action == "type":
        import pyautogui
        pyautogui.write(value)
        return f"Typed: {value}"
    elif action == "screenshot":
        import pyautogui
        pyautogui.screenshot("screenshot.png")
        return "Screenshot saved"
    elif action == "hotkey":
        import pyautogui
        keys = value.split("+")
        pyautogui.hotkey(*keys)
        return f"Pressed: {value}"

    return f"Computer action '{action}' executed"