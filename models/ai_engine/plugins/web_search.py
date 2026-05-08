import json
import urllib.request
import urllib.parse

def _load_config():
    with open("config.json", "r") as f:
        return json.load(f).get("search", {})

def search_serper(query, num=5):
    """Google results via Serper.dev API."""
    cfg = _load_config()
    api_key = cfg.get("serper_api_key", "")
    if not api_key or api_key == "YOUR_SERPER_KEY_HERE":
        return []
    try:
        url = "https://google.serper.dev/search"
        data = json.dumps({"q": query, "num": num}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
        items = result.get("organic", [])
        return [{
            "title": i.get("title", ""),
            "body": i.get("snippet", ""),
            "href": i.get("link", "")
        } for i in items[:num]]
    except Exception as e:
        return []

def search_brave(query, num=5):
    """Brave Search API."""
    cfg = _load_config()
    api_key = cfg.get("brave_api_key", "")
    if not api_key or api_key == "YOUR_BRAVE_KEY_HERE":
        return []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.search.brave.com/res/v1/web/search?q={encoded}&count={num}"
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key
            }
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
        items = result.get("web", {}).get("results", [])
        return [{
            "title": i.get("title", ""),
            "body": i.get("description", ""),
            "href": i.get("url", "")
        } for i in items[:num]]
    except Exception as e:
        return []

def search_wikipedia(query):
    """Wikipedia fallback - always works."""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        req = urllib.request.Request(url, headers={"User-Agent": "AIEngine/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return [{
            "title": data.get("title", query),
            "body": data.get("extract", "No summary."),
            "href": data.get("content_urls", {}).get("desktop", {}).get("page", "")
        }]
    except Exception as e:
        return []
 
def search(query, num=5):
    """Main search - tries all engines in order."""
    cfg = _load_config()
    primary = cfg.get("primary", "serper")
    
    # Try primary
    if primary == "serper":
        results = search_serper(query, num)
        if results:
            return results
    
    # Try Brave
    results = search_brave(query, num)
    if results:
        return results
    
    # Try DuckDuckGo
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num))
        if results:
            return results
    except Exception as e:
        pass
    
    # Final fallback: Wikipedia
    return search_wikipedia(query)

def find_download(name):
    """Find official download page."""
    return search(f"{name} official download site Windows 11")
