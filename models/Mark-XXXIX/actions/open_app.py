"""Open application action."""

def open_app(parameters, response, player):
    app_name = parameters.get("app_name", "")
    try:
        import subprocess
        subprocess.Popen(["start", app_name], shell=True)
        return f"Opened {app_name}"
    except Exception as e:
        return f"Error opening {app_name}: {e}"