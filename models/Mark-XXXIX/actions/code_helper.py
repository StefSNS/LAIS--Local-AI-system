"""Code helper action."""

def code_helper(parameters, player, speak=None):
    action = parameters.get("action", "explain")
    description = parameters.get("description", "")
    file_path = parameters.get("file_path", "")

    if player:
        player.ui.write_log(f"Code: {action}")

    return f"Code helper - {action}: {description or file_path}"