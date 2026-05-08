from duckduckgo_search import DDGS
import os
import urllib.request
import json


def search_wikipedia(topic):
    """Fallback search using Wikipedia API."""
    try:
        # Try exact topic first, then try simplified versions
        topics_to_try = [
            topic,
            topic.replace(' ', '_'),
            topic.split(' techniques')[0] if ' techniques' in topic else topic,
            topic.split(' optimization')[0] if ' optimization' in topic else topic
        ]
        
        for t in topics_to_try:
            try:
                url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{t}"
                req = urllib.request.Request(url, headers={'User-Agent': 'AIEngine/1.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read())
                    if data.get('extract') and data.get('extract') != 'No description available.':
                        return [{
                            'title': data.get('title', topic),
                            'body': data.get('extract', 'No summary available.'),
                            'href': data.get('content_urls', {}).get('desktop', {}).get('page', '')
                        }]
            except Exception:
                continue
        return []
    except Exception:
        return []

def research_and_save(topic):
    """Search with DuckDuckGo, fallback to Wikipedia if 0 results."""
    try:
        results = []

        # Try DuckDuckGo first
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    topic,
                    region='wt-wt',
                    safesearch='off',
                    max_results=5
                ))
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")
            results = []

        # Fallback to Wikipedia with multiple attempts
        if not results:
            results = search_wikipedia(topic)
            
            # Try simpler search if still no results
            if not results and ' ' in topic:
                simpler_topic = ' '.join(topic.split(' ')[:3])  # First 3 words
                results = search_wikipedia(simpler_topic)

        os.makedirs('knowledge', exist_ok=True)
        safe_name = topic.replace(' ', '_').replace('/', '_')[:80]
        filename = f"knowledge/{safe_name}.md"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Research: {topic}\n\n")
            if not results:
                f.write("> No results found from any source.\n")
                f.write("\n## Attempted Topic\n")
                f.write(f"{topic}\n")
            else:
                source = "Wikipedia" if len(results) == 1 else "DuckDuckGo"
                f.write(f"> Source: {source}\n\n")
                for r in results:
                    f.write(f"### {r.get('title', 'No Title')}\n")
                    f.write(f"{r.get('body', 'No content.')}\n")
                    f.write(f"Source: {r.get('href', 'No link')}\n\n")

        return f"Research complete. {len(results)} items saved to {filename}"

    except Exception as e:
        return f"Research failed: {e}"