import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unified_layer.unified_search import load_unified_search

s = load_unified_search()

queries = [
    "OWASP injection attack",
    "Node.js streams",
    "React hooks",
    "LangChain agents",
    "Rust ownership",
    "FastAPI async",
    "CrewAI multi-agent",
]

for q in queries:
    print(f"\n=== '{q}' ===")
    r = s.search_all(q, max_results_per_source=2)
    for source, items in r.items():
        if items:
            print(f"  {source} ({len(items)}):")
            for x in items[:2]:
                title = x.get("title", x.get("key", ""))
                content = x.get("text", x.get("value", x.get("content", "")))[:80]
                score = x.get("score", x.get("fts_rank", ""))
                print(f"    [{score}] {title}: {content}")

s.close()
