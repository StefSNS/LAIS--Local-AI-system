import webbrowser
from urllib.parse import quote_plus

def weather_report(parameters: dict) -> str:
    city = parameters.get("city")
    time = parameters.get("time", "today")

    if not city or not isinstance(city, str):
        return "Please specify a city for the weather report."

    city = city.strip()
    if not time or not isinstance(time, str):
        time = "today"
    else:
        time = time.strip()

    search_query = f"weather in {city} {time}"
    encoded_query = quote_plus(search_query)
    url = f"https://www.google.com/search?q={encoded_query}"

    try:
        webbrowser.open(url)
        return f"Showing weather for {city}, {time}."
    except Exception:
        return f"Could not open weather report for {city}."
