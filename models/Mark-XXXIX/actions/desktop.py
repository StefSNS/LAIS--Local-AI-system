"""Desktop control action."""

def desktop_control(parameters, player):
    action = parameters.get("action", "")

    if player:
        player.ui.write_log(f"Desktop: {action}")

    return f"Desktop action '{action}' executed"