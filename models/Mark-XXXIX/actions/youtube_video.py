"""Youtube video action."""

def youtube_video(parameters, player, response=None):
    action = parameters.get("action", "play")
    query = parameters.get("query", "")

    if player:
        player.ui.write_log(f"YouTube: {action} - {query}")

    if action == "play" and query:
        return f"Playing YouTube video: {query}"
    elif action == "search":
        return f"YouTube search: {query}"

    return f"YouTube action '{action}' executed"