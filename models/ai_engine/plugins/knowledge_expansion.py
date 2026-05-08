"""
Knowledge Expansion Pipeline - Downloads and ingests technical documentation
into the knowledge vault for semantic search.

Target domains:
- Server-side development (Node.js, Python FastAPI, Go, Rust)
- Web development (React, TypeScript, Web APIs, CSS)
- Cybersecurity dev stack (OWASP, pentesting tools, secure coding)
- AI agent development (LangChain, MCP, crewAI, AutoGen)
- Additional languages (Rust, Go, TypeScript, Zig)
"""

import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

VAULT_PATH = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge")
INGESTION_PATH = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge\ingested")
EXPANSION_PATH = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge\expansion")
INGESTION_PATH.mkdir(parents=True, exist_ok=True)
EXPANSION_PATH.mkdir(parents=True, exist_ok=True)


DOC_SOURCES = {
    "server_nodejs": {
        "name": "Node.js Documentation",
        "category": "server",
        "urls": [
            "https://raw.githubusercontent.com/nodejs/node/main/doc/api/fs.md",
            "https://raw.githubusercontent.com/nodejs/node/main/doc/api/http.md",
            "https://raw.githubusercontent.com/nodejs/node/main/doc/api/stream.md",
        ],
        "topics": ["filesystem", "http_server", "streams", "events", "modules"],
    },
    "server_fastapi": {
        "name": "FastAPI Python Framework",
        "category": "server",
        "urls": [
            "https://raw.githubusercontent.com/fastapi/fastapi/master/docs/en/docs/index.md",
            "https://raw.githubusercontent.com/fastapi/fastapi/master/docs/en/docs/tutorial/index.md",
        ],
        "topics": ["fastapi", "python_backend", "rest_api", "async", "pydantic"],
    },
    "server_go": {
        "name": "Go Programming",
        "category": "server",
        "urls": [
            "https://raw.githubusercontent.com/golang/go/master/README.md",
        ],
        "topics": ["go", "golang", "concurrency", "goroutines", "stdlib"],
    },
    "server_rust": {
        "name": "Rust Programming",
        "category": "server",
        "urls": [
            "https://raw.githubusercontent.com/rust-lang/book/master/src/README.md",
        ],
        "topics": ["rust", "ownership", "borrowing", "traits", "cargo"],
    },
    "web_typescript": {
        "name": "TypeScript Documentation",
        "category": "web",
        "urls": [
            "https://raw.githubusercontent.com/microsoft/TypeScript/main/README.md",
        ],
        "topics": ["typescript", "types", "interfaces", "generics", "decorators"],
    },
    "web_react": {
        "name": "React Documentation",
        "category": "web",
        "urls": [
            "https://raw.githubusercontent.com/facebook/react/main/README.md",
        ],
        "topics": ["react", "hooks", "components", "state", "jsx"],
    },
    "security_owasp": {
        "name": "OWASP Top 10",
        "category": "security",
        "urls": [
            "https://raw.githubusercontent.com/OWASP/Top10/master/README.md",
        ],
        "topics": ["owasp", "injection", "xss", "csrf", "authentication", "security"],
    },
    "security_pentest": {
        "name": "Pentesting Methodology",
        "category": "security",
        "urls": [
            "https://raw.githubusercontent.com/enaqx/awesome-pentest/master/README.md",
        ],
        "topics": ["pentesting", "reconnaissance", "exploitation", "post_exploitation", "tools"],
    },
    "security_secure_coding": {
        "name": "Secure Coding Practices",
        "category": "security",
        "urls": [
            "https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/README.md",
        ],
        "topics": ["secure_coding", "input_validation", "encryption", "authentication", "logging"],
    },
    "ai_agents_langchain": {
        "name": "LangChain Agent Framework",
        "category": "ai_agents",
        "urls": [
            "https://raw.githubusercontent.com/langchain-ai/langchain/master/README.md",
        ],
        "topics": ["langchain", "chains", "agents", "tools", "memory", "llms"],
    },
    "ai_agents_mcp": {
        "name": "Model Context Protocol",
        "category": "ai_agents",
        "urls": [
            "https://raw.githubusercontent.com/modelcontextprotocol/specification/main/README.md",
        ],
        "topics": ["mcp", "model_context_protocol", "tools", "resources", "prompts"],
    },
    "ai_agents_crewai": {
        "name": "CrewAI Multi-Agent Framework",
        "category": "ai_agents",
        "urls": [
            "https://raw.githubusercontent.com/crewAIInc/crewAI/main/README.md",
        ],
        "topics": ["crewai", "multi_agent", "roles", "tasks", "processes", "collaboration"],
    },
    "ai_agents_autogen": {
        "name": "AutoGen Conversational Agents",
        "category": "ai_agents",
        "urls": [
            "https://raw.githubusercontent.com/microsoft/autogen/main/README.md",
        ],
        "topics": ["autogen", "conversational_agents", "multi_agent", "code_execution"],
    },
}


class KnowledgeExpander:
    """Downloads and ingests technical documentation into the knowledge vault."""

    def __init__(self):
        self.results: List[Dict] = []
        self.total_downloaded = 0
        self.total_bytes = 0

    def fetch_url(self, url: str, timeout: int = 30) -> Optional[str]:
        """Fetch content from a URL."""
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 KnowledgeExpander/1.0"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"  [WARN] Failed to fetch {url}: {e}")
            return None

    def ingest_source(self, source_key: str, source: Dict) -> Dict:
        """Download and ingest a documentation source."""
        print(f"\n--- {source['name']} ---")

        result = {
            "source": source_key,
            "name": source["name"],
            "category": source["category"],
            "topics": source["topics"],
            "urls_processed": 0,
            "urls_failed": 0,
            "bytes_downloaded": 0,
            "files_created": [],
            "started_at": datetime.now().isoformat(),
        }

        for i, url in enumerate(source["urls"]):
            content = self.fetch_url(url)
            if not content:
                result["urls_failed"] += 1
                continue

            result["urls_processed"] += 1
            result["bytes_downloaded"] += len(content.encode("utf-8"))
            self.total_downloaded += 1
            self.total_bytes += len(content.encode("utf-8"))

            filename = f"{source_key}_{i}.md"
            output_file = EXPANSION_PATH / filename

            header = f"""# {source['name']}

**Source**: {url}
**Category**: {source['category']}
**Topics**: {', '.join(source['topics'])}
**Ingested**: {datetime.now().isoformat()}

---

"""
            output_file.write_text(header + content, encoding="utf-8")
            result["files_created"].append(filename)
            print(f"  [+] Downloaded: {filename} ({len(content):,} chars)")

        result["completed_at"] = datetime.now().isoformat()
        self.results.append(result)
        return result

    def ingest_all(self, categories: Optional[List[str]] = None) -> List[Dict]:
        """Ingest all sources or filter by category."""
        if categories:
            sources = {k: v for k, v in DOC_SOURCES.items() if v["category"] in categories}
        else:
            sources = DOC_SOURCES

        print(f"Knowledge Expansion: {len(sources)} sources to process")
        print(f"Target directory: {EXPANSION_PATH}")

        results = []
        for key, source in sources.items():
            result = self.ingest_source(key, source)
            results.append(result)
            time.sleep(0.5)

        return results

    def get_existing_docs(self) -> List[Dict]:
        """List already ingested documentation."""
        docs = []
        if EXPANSION_PATH.exists():
            for f in sorted(EXPANSION_PATH.glob("*.md")):
                stat = f.stat()
                docs.append({
                    "file": f.name,
                    "size_kb": round(stat.st_size / 1024, 1),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        return docs

    def get_summary(self) -> Dict:
        """Get expansion summary."""
        existing = self.get_existing_docs()
        return {
            "total_sources": len(DOC_SOURCES),
            "sources_by_category": {},
            "total_docs_ingested": len(existing),
            "total_docs_size_mb": round(sum(d["size_kb"] for d in existing) / 1024, 2),
            "last_run_results": self.results,
            "existing_docs": existing,
        }

    def rebuild_index(self):
        """Rebuild txtai semantic index after expansion."""
        try:
            import sys
            plugin_dir = Path(__file__).resolve().parent.parent
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir))
            from plugins.semantic_search import load_txtai_search
            print("\n[KnowledgeExpander] Rebuilding txtai index...")
            search = load_txtai_search()
            search.rebuild()
            print("[KnowledgeExpander] Index rebuilt successfully")
            search = load_txtai_search()
            stats = search.get_stats()
            print(f"[KnowledgeExpander] Index now has {stats.get('documents', 0)} documents")
        except Exception as e:
            print(f"[KnowledgeExpander] Failed to rebuild index: {e}")

    def trigger_auto_ingestion(self):
        """Trigger automated ingestion system after expansion."""
        try:
            import sys
            plugin_dir = Path(__file__).resolve().parent.parent
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir))
            from plugins.ingestion_triggers import load_trigger
            print("\n[KnowledgeExpander] Running ingestion trigger...")
            trigger = load_trigger()
            result = trigger.trigger_rebuild(force=True)
            if result.get("success"):
                print(f"[KnowledgeExpander] Auto-ingestion complete: {result.get('documents_indexed', 0)} docs indexed")
            else:
                print(f"[KnowledgeExpander] Auto-ingestion result: {result}")
        except Exception as e:
            print(f"[KnowledgeExpander] Failed to trigger auto-ingestion: {e}")


def load_expander() -> KnowledgeExpander:
    """Factory function."""
    return KnowledgeExpander()


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    expander = load_expander()

    print("=== Knowledge Expansion Pipeline ===")
    print(f"Sources available: {len(DOC_SOURCES)}")
    print(f"Categories: {set(s['category'] for s in DOC_SOURCES.values())}")

    existing = expander.get_existing_docs()
    if existing:
        print(f"\nExisting docs: {len(existing)} ({sum(d['size_kb'] for d in existing) / 1024:.1f}MB)")
        for d in existing[:5]:
            print(f"  - {d['file']} ({d['size_kb']}KB)")

    print("\n--- Running expansion ---")
    results = expander.ingest_all()

    print(f"\n--- Summary ---")
    print(f"Sources processed: {len(results)}")
    total_urls = sum(r["urls_processed"] for r in results)
    total_failed = sum(r["urls_failed"] for r in results)
    total_bytes = sum(r["bytes_downloaded"] for r in results)
    print(f"URLs downloaded: {total_urls}")
    print(f"URLs failed: {total_failed}")
    print(f"Total data: {total_bytes / 1024:.1f}KB")

    print("\n--- Rebuilding search index ---")
    expander.rebuild_index()

    print("\n--- Triggering auto-ingestion ---")
    expander.trigger_auto_ingestion()
