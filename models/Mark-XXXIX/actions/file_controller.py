"""File controller action."""

def file_controller(parameters, player):
    action = parameters.get("action", "")
    path = parameters.get("path", "")
    destination = parameters.get("destination", "")
    content = parameters.get("content", "")

    from pathlib import Path

    if player:
        player.ui.write_log(f"File: {action} {path}")

    if action == "read" and path:
        try:
            return Path(path).read_text()
        except Exception as e:
            return f"Error reading {path}: {e}"
    elif action == "write" and path and content:
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(content)
            return f"Wrote to {path}"
        except Exception as e:
            return f"Error writing {path}: {e}"
    elif action == "list":
        try:
            items = list(Path(path).glob("*")) if path else list(Path(".").glob("*"))
            return "\n".join(str(p.name) for p in items[:20])
        except Exception as e:
            return f"Error listing {path}: {e}"

    return f"File action '{action}' executed"