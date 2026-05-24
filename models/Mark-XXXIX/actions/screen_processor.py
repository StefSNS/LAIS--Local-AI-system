"""Screen processor action."""

def screen_process(parameters, player, session_memory=None, response=None):
    angle = parameters.get("angle", "screen")
    text = parameters.get("text", "")

    if player:
        player.ui.write_log(f"Screen capture: {angle}")

    return "Screen captured. [Vision processing placeholder]"

def screen_capture():
    """Capture screen and return image path."""
    import mss
    import os
    with mss.mss() as s:
        s.shot(output="screen.png")
    return os.path.abspath("screen.png")