"""Browser control action."""

def browser_control(parameters, player):
    action = parameters.get("action", "")
    url = parameters.get("url", "")
    query = parameters.get("query", "")

    if player:
        player.ui.write_log(f"Browser: {action}")

    if action == "go_to" and url:
        return f"Navigating to {url}"
    elif action == "search" and query:
        return f"Searching for: {query}"
    return f"Browser action '{action}' executed"