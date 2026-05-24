"""Computer settings action."""

def computer_settings(parameters, player):
    action = parameters.get("action", "")
    value = parameters.get("value", "")

    if player:
        player.ui.write_log(f"Settings: {action}")

    return f"Settings action '{action}' executed"