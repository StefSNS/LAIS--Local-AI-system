"""Web search action."""

def web_search(parameters, player):
    query = parameters.get("query", "")
    mode = parameters.get("mode", "search")

    if player:
        player.ui.write_log(f"Searching: {query}")

    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if results:
            return "\n".join(f"- {r['title']}: {r['href']}" for r in results)
        return "No results found"
    except Exception as e:
        return f"Search error: {e}"