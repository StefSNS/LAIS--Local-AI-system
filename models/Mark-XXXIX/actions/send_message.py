"""Send message action."""

def send_message(parameters, player, session_memory=None, response=None):
    receiver = parameters.get("receiver", "")
    message_text = parameters.get("message_text", "")
    platform = parameters.get("platform", "")

    if player:
        player.ui.write_log(f"Message to {receiver} via {platform}")

    return f"Message sent to {receiver}"