"""File processor action."""

def file_processor(parameters, player, speak=None):
    file_path = parameters.get("file_path", "")
    action = parameters.get("action", "info")
    instruction = parameters.get("instruction", "")

    if player:
        player.ui.write_log(f"File: {action} - {file_path}")

    if action == "info":
        from pathlib import Path
        p = Path(file_path)
        if p.exists():
            return f"File: {p.name}, Size: {p.stat().st_size} bytes"
        return "File not found"

    return f"File '{action}' processed"