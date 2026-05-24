"""Weather report action."""

def weather_action(parameters, player):
    city = parameters.get("city", "")
    if player:
        player.ui.write_log(f"Fetching weather for {city}...")
    return f"Weather for {city}: Partly cloudy, 68-75F"