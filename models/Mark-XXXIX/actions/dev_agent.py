"""Dev agent action."""

def dev_agent(parameters, player, speak=None):
    description = parameters.get("description", "")

    if player:
        player.ui.write_log(f"Dev: Building - {description[:50]}...")

    return f"Project created: {description[:30]}..."