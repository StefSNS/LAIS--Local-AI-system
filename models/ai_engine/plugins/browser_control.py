import os
import sys
import json
import urllib.parse
import subprocess
import importlib.util

def get_browser():
    """Find the default browser on Windows 11."""
    browsers = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    for b in browsers:
        if os.path.exists(b):
            return b
    return None

def open_url(url):
    """Open a URL in the default browser."""
    if not url.startswith("http"):
        url = "https://" + url
    browser = get_browser()
    if browser:
        subprocess.Popen([browser, url])
        return f"Opened: {url}"
    else:
        os.startfile(url)
        return f"Opened: {url}"

def search_and_open(query):
    """Search and open the top result in browser."""
    sys.path.insert(0, "plugins")
    spec = importlib.util.spec_from_file_location("web_search", "plugins/web_search.py")
    ws = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ws)
    
    results = ws.search(query)
    if results:
        url = results[0].get("href", "")
        if url:
            open_url(url)
            return f"Opened top result: {url}"
    return "No results found to open."

def open_search_engine(query, engine="google"):
    """Open a search query directly in browser - detects site names."""
    query = query.strip()
    
    # Known site shortcuts
    site_shortcuts = {
        "stackoverflow": "https://stackoverflow.com/search?q=",
        "stack overflow": "https://stackoverflow.com/search?q=",
        "github": "https://github.com/search?q=",
        "youtube": "https://www.youtube.com/results?search_query=",
        "reddit": "https://www.reddit.com/search/?q=",
        "wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search=",
        "google": "https://www.google.com/search?q=",
        "bing": "https://www.bing.com/search?q=",
        "pypi": "https://pypi.org/search/?q=",
        "docs.python": "https://docs.python.org/3/search.html?q=",
        "huggingface": "https://huggingface.co/models?search="
    }
    
    lower_query = query.lower()
    
    # Check if query starts with a known site
    for site, base_url in site_shortcuts.items():
        if lower_query.startswith(site):
            # Extract the search term after the site name
            search_term = query[len(site):].strip().lstrip("and").strip()
            if search_term:
                encoded = urllib.parse.quote(search_term)
                url = base_url + encoded
            else:
                url = base_url.split("?")[0]
            return open_url(url)
    
    # Check if it contains "on [site]" or "at [site]"
    for site, base_url in site_shortcuts.items():
        if f"on {site}" in lower_query or f"at {site}" in lower_query:
            # Extract search term
            search_term = lower_query.replace(f"on {site}", "").replace(f"at {site}", "").strip()
            encoded = urllib.parse.quote(search_term)
            url = base_url + encoded
            return open_url(url)
    
    # Default: Google search
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    return open_url(url)

def open_download_page(software_name):
    """Search for and open the download page of software."""
    query = f"{software_name} official download site"
    return search_and_open(query)
