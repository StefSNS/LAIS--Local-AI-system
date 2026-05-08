import json
import re
import sys
import subprocess
import platform
from datetime import datetime, timedelta
from pathlib import Path

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent / "Mark-XXXV"

def _parse_date(raw: str) -> str:
    raw = raw.strip()
    if re.match(r"\d{4}-\d{2}-\d{2}", raw):
        return raw
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    today = datetime.now()
    lower = raw.lower()
    relative_map = {"today": today, "tomorrow": today + timedelta(days=1), "bugün": today, "yarın": today + timedelta(days=1)}
    for key, val in relative_map.items():
        if key in lower:
            return val.strftime("%Y-%m-%d")
    try:
        import google.generativeai as genai
        sys.path.insert(0, str(get_base_dir()))
        from utils.api_keys import get_gemini_api_key
        genai.configure(api_key=get_gemini_api_key())
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(f"Today is {today.strftime('%Y-%m-%d')}. Convert to YYYY-MM-DD: '{raw}'. Return ONLY the date.")
        result = response.text.strip()
        if re.match(r"\d{4}-\d{2}-\d{2}", result):
            return result
    except Exception:
        pass
    month_map = {"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,"july":7,"august":8,"september":9,"october":10,"november":11,"december":12,"ocak":1,"şubat":2,"mart":3,"nisan":4,"mayıs":5,"haziran":6,"temmuz":7,"ağustos":8,"eylül":9,"ekim":10,"kasım":11,"aralık":12}
    for month_name, month_num in month_map.items():
        if month_name in lower:
            day_match = re.search(r"\d{1,2}", raw)
            if day_match:
                day = int(day_match.group())
                year = today.year if month_num >= today.month else today.year + 1
                return f"{year}-{month_num:02d}-{day:02d}"
    return today.strftime("%Y-%m-%d")

def _build_url(origin, destination, date, return_date=None, passengers=1, cabin="economy"):
    cabin_map = {"economy": "1", "premium": "2", "business": "3", "first": "4"}
    cabin_code = cabin_map.get(cabin.lower(), "1")
    base = "https://www.google.com/travel/flights"
    if return_date:
        return f"{base}?q=Flights+from+{origin}+to+{destination}+on+{date}+returning+{return_date}&curr=TRY"
    return f"{base}?q=Flights+from+{origin}+to+{destination}+on+{date}&curr=TRY"

def flight_finder(parameters: dict) -> str:
    params = parameters or {}
    origin = params.get("origin", "").strip()
    destination = params.get("destination", "").strip()
    date_raw = params.get("date", "").strip()
    return_raw = params.get("return_date", "").strip()
    passengers = int(params.get("passengers", 1))
    cabin = params.get("cabin", "economy").strip()
    save = params.get("save", False)

    if not origin or not destination:
        return "Please provide both origin and destination."
    if not date_raw:
        return "Please provide a departure date."

    date = _parse_date(date_raw)
    return_date = _parse_date(return_raw) if return_raw else None

    try:
        from plugins.browser_control import open_url
        url = _build_url(origin, destination, date, return_date, passengers, cabin)
        open_url(url)
        return f"Opened flight search: {origin} → {destination} on {date}"
    except Exception as e:
        return f"Flight search failed: {e}"
