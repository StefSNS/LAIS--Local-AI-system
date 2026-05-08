import sys
import os
import json
import urllib.request
import importlib.util
from urllib.parse import urlparse

def get_page_text(url, timeout=10):
    """Fetch and extract clean text from a webpage."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw_html = r.read()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw_html, "lxml")
        
        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
            tag.decompose()
        
        # Get main content
        main = soup.find("main") or soup.find("article") or soup.find("div", {"id": "content"}) or soup.body
        
        if main:
            text = main.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)
        
        # Clean up whitespace
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        clean = " ".join(lines)
        
        # Limit to 3000 chars for RAM efficiency
        return clean[:3000]
    
    except Exception as e:
        return f"Could not scrape {url}: {e}"

def summarize_text(text, topic, llm_func=None):
    """Summarize scraped text using LAIS LLM."""
    if not text or len(text) < 50:
        return "No content to summarize."
    
    if llm_func:
        prompt = f"Summarize this content about {topic} in 3-5 bullet points:\n\n{text[:2000]}"
        return llm_func(prompt)
    
    # Fallback: return first 500 chars as preview
    return text[:500] + "..."

def scrape_and_save(topic, max_urls=3):
    """Search, scrape top results, summarize, save to knowledge."""
    sys.path.insert(0, "plugins")
    
    # Get search results
    spec = importlib.util.spec_from_file_location("web_search", "plugins/web_search.py")
    ws = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ws)
    results = ws.search(topic, num=max_urls)
    
    if not results:
        return f"No results found for: {topic}"
    
    os.makedirs("knowledge", exist_ok=True)
    safe_name = topic.replace(" ", "_").replace("/", "_").replace(":", "").replace(".", "_")[:60]
    safe_name = safe_name.strip("_")
    filename = f"knowledge/scraped_{safe_name}.md"
    
    report = []
    report.append(f"# Deep Research: {topic}\n")
    report.append(f"> Scraped {len(results)} sources\n")
    
    successful = 0
    
    for i, result in enumerate(results[:max_urls]):
        url = result.get("href", "")
        title = result.get("title", "Unknown")
        
        if not url:
            continue
        
        report.append(f"\n## Source {i+1}: {title}")
        report.append(f"URL: {url}\n")
        
        # Scrape the page
        content = get_page_text(url)
        
        if "Could not scrape" in content:
            report.append(f"> {content}\n")
            continue
        
        # Add content preview
        report.append(f"### Content Preview")
        report.append(content[:1500])
        report.append("\n---\n")
        successful += 1
    
    # Write to knowledge
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    return f"Deep research complete. Scraped {successful}/{len(results)} sources. Saved to {filename}"

def scrape_url(url):
    """Scrape a single URL and return its text."""
    return get_page_text(url)
