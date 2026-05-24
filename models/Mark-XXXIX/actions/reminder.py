"""Reminder action."""

def reminder(parameters, player):
    date = parameters.get("date", "")
    time = parameters.get("time", "")
    message = parameters.get("message", "")

    if player:
        player.ui.write_log(f"Reminder: {message}")

    return f"Reminder set for {date} at {time}: {message}"