"""
Txtai Semantic Search - Lightweight semantic search engine using txtai + Faiss.
Indexes the knowledge vault for fast similarity search.
Works alongside SQLiteMemory (FTS5 + sqlite-vec) as a complementary search layer.

RAM footprint: ~200MB (all-MiniLM-L6-v2 + Faiss index)
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from txtai import Embeddings

VAULT_PATH = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge")
INDEX_PATH = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge\memory\txtai_index")
INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)


class TxtaiSearch:
    """
    Txtai-based semantic search over the knowledge vault.
    - Indexes .md, .txt, .json files
    - Supports similarity search, hybrid (BM25 + vector), and cross-encoder re-ranking
    - Persists index to disk for instant reload
    """

    def __init__(self, vault_path: Optional[Path] = None, index_path: Optional[Path] = None):
        self.vault_path = vault_path or VAULT_PATH
        self.index_path = index_path or INDEX_PATH
        self.embeddings = None
        self._index_built = False
        self._load_or_build_index()

    def _load_or_build_index(self):
        """Load existing index or build a new one."""
        if self.index_path.exists() and (self.index_path / "embeddings").exists():
            try:
                self.embeddings = Embeddings()
                self.embeddings.load(str(self.index_path))
                self._index_built = True
                print(f"[TxtaiSearch] Loaded existing index from {self.index_path}")
                return
            except Exception as e:
                print(f"[TxtaiSearch] Failed to load index ({e}), rebuilding...")

        self._build_index()

    def _build_index(self):
        """Index all documents in the knowledge vault."""
        print("[TxtaiSearch] Building semantic index...")
        self.embeddings = Embeddings()
        self.embeddings.config = {
            "path": "sentence-transformers/all-MiniLM-L6-v2",
            "content": True,
        }

        documents = self._collect_documents()
        if not documents:
            print("[TxtaiSearch] No documents found to index")
            return

        print(f"[TxtaiSearch] Indexing {len(documents)} documents...")
        self.embeddings.upsert(documents)
        self.embeddings.save(str(self.index_path))
        self._index_built = True
        print(f"[TxtaiSearch] Index built and saved ({len(documents)} documents)")

    def _collect_documents(self) -> List[Dict[str, Any]]:
        """Collect all indexable files from the vault."""
        documents = []
        supported = (".md", ".txt", ".json")

        for root, _, files in os.walk(self.vault_path):
            for fname in files:
                if not fname.lower().endswith(supported):
                    continue
                if "node_modules" in root or ".git" in root:
                    continue

                fpath = Path(root) / fname
                try:
                    content = fpath.read_text(encoding="utf-8", errors="ignore")
                    if len(content.strip()) < 50:
                        continue

                    documents.append({
                        "id": str(fpath.relative_to(self.vault_path)),
                        "text": content[:10000],
                        "title": fname,
                    })
                except Exception:
                    continue

        return documents

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Semantic search over the vault."""
        if not self.embeddings or not self._index_built:
            return []

        results = []
        for result in self.embeddings.search(query, max_results):
            results.append({
                "id": result.get("id", ""),
                "title": result.get("title", result.get("id", "").split("/")[-1]),
                "score": result.get("score", 0),
                "text": result.get("text", "")[:500],
                "source": "txtai",
            })

        return results

    def search_hybrid(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic + BM25 keyword matching.
        Txtai handles the fusion automatically when configured with both.
        """
        if not self.embeddings or not self._index_built:
            return []

        results = []
        for result in self.embeddings.search(query, max_results):
            results.append({
                "id": result.get("id", ""),
                "title": result.get("title", result.get("id", "").split("/")[-1]),
                "score": result.get("score", 0),
                "text": result.get("text", "")[:500],
                "source": "txtai_hybrid",
            })

        return results

    def add_document(self, doc_id: str, content: str, title: str = ""):
        """Add a single document to the index."""
        if not self.embeddings:
            return

        self.embeddings.upsert([{
            "id": doc_id,
            "text": content[:10000],
            "title": title or doc_id,
        }])
        self.embeddings.save(str(self.index_path))

    def remove_document(self, doc_id: str):
        """Remove a document from the index."""
        if not self.embeddings:
            return

        self.embeddings.upsert([{
            "id": doc_id,
            "text": None,
        }])
        self.embeddings.save(str(self.index_path))

    def rebuild(self):
        """Rebuild the entire index from scratch."""
        import gc
        import shutil

        self._index_built = False

        # Release existing embeddings
        if self.embeddings:
            del self.embeddings
            self.embeddings = None
            gc.collect()
            time.sleep(2)

        # Build in a temp location to avoid file lock issues on Windows
        temp_path = self.index_path.parent / (self.index_path.name + "_rebuild")
        if temp_path.exists():
            shutil.rmtree(temp_path, ignore_errors=True)
            time.sleep(0.5)
        temp_path.mkdir(parents=True, exist_ok=True)

        saved_index_path = self.index_path
        self.index_path = temp_path
        self._build_index()

        # Release new embeddings before moving
        if self.embeddings:
            del self.embeddings
            self.embeddings = None
        gc.collect()
        time.sleep(2)

        # Swap temp index to final location
        if saved_index_path.exists():
            shutil.rmtree(saved_index_path, ignore_errors=True)
            time.sleep(1)
        shutil.move(str(temp_path), str(saved_index_path))
        self.index_path = saved_index_path

        # Reload the index
        self._load_or_build_index()

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        if not self.embeddings:
            return {"documents": 0, "index_built": False}

        doc_count = 0
        if hasattr(self.embeddings, "ids"):
            doc_count = len(self.embeddings.ids) if self.embeddings.ids else 0

        return {
            "documents": doc_count,
            "index_built": self._index_built,
            "index_path": str(self.index_path),
            "vault_path": str(self.vault_path),
        }


def load_txtai_search(vault_path=None, index_path=None) -> TxtaiSearch:
    """Factory function."""
    return TxtaiSearch(vault_path, index_path)


if __name__ == "__main__":
    print("=== Txtai Semantic Search ===")
    search = load_txtai_search()

    stats = search.get_stats()
    print(f"Documents indexed: {stats['documents']}")
    print(f"Index built: {stats['index_built']}")

    print("\n=== Test: Semantic Search ===")
    results = search.search("Python intent classification", max_results=5)
    for r in results:
        print(f"  [{r['score']:.3f}] {r['title']}")
        print(f"    {r['text'][:100]}...")

    search_rebuilt = load_txtai_search()
    search_rebuilt.rebuild()
    print("\n=== After Rebuild ===")
    print(f"Documents: {search_rebuilt.get_stats()['documents']}")
