"""Game updater action."""

def game_updater(parameters, player, speak=None):
    action = parameters.get("action", "update")
    platform = parameters.get("platform", "both")
    game_name = parameters.get("game_name", "")

    if player:
        player.ui.write_log(f"Game: {action} - {game_name}")

    return f"Game action '{action}' for {game_name} on {platform}"