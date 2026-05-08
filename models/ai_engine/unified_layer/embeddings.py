"""
Lightweight Local Embeddings - Semantic search for the Unified Brain vault
Uses all-MiniLM-L6-v2 (~90MB) for true semantic search, fully offline.
Falls back to TF-IDF if model is unavailable.
"""

import json
import os
import numpy as np
from pathlib import Path
from datetime import datetime
from threading import Lock

VAULT_PATH = Path(os.environ.get("LAIS_VAULT_PATH", r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain"))
MEMORY_DIR = Path(r"str(Path(__file__).resolve().parent.parent)\knowledge\memory")
EMBEDDINGS_FILE = MEMORY_DIR / "vault_embeddings.json"
LOCK = Lock()

USE_SENTENCE_TRANSFORMERS = False
MODEL = None
EMBEDDINGS = {}
NOTE_VECTORS = {}

try:
    from sentence_transformers import SentenceTransformer
    MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    USE_SENTENCE_TRANSFORMERS = True
    print(f"[Embeddings] Loaded all-MiniLM-L6-v2 (semantic search active)")
except Exception as e:
    print(f"[Embeddings] Using TF-IDF fallback ({e})")


class TFIDFEmbedder:
    """Simple TF-IDF fallback when sentence-transformers unavailable."""
    
    def __init__(self):
        self.vocabulary = {}
        self.doc_vectors = {}
        self.idf = {}
    
    def fit(self, documents):
        """Build vocabulary and IDF from documents."""
        doc_freq = {}
        total_docs = len(documents)
        
        for i, doc in enumerate(documents):
            words = doc.lower().split()
            word_set = set(words)
            for word in word_set:
                doc_freq[word] = doc_freq.get(word, 0) + 1
            
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            norm = sum(v**2 for v in word_counts.values()) ** 0.5
            if norm > 0:
                word_counts = {k: v/norm for k, v in word_counts.items()}
            
            self.doc_vectors[i] = word_counts
        
        for word, freq in doc_freq.items():
            self.idf[word] = np.log((1 + total_docs) / (1 + freq)) + 1
        
        self.vocabulary = list(self.idf.keys())
    
    def transform(self, text):
        """Transform text to TF-IDF vector."""
        words = text.lower().split()
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        norm = sum(v**2 for v in word_counts.values()) ** 0.5
        if norm > 0:
            word_counts = {k: v/norm for k, v in word_counts.items()}
        
        return {word: word_counts.get(word, 0) * self.idf.get(word, 1) 
                for word in self.vocabulary if word in word_counts}
    
    def cosine_similarity(self, vec1, vec2):
        """Compute cosine similarity between two vectors."""
        common_keys = set(vec1.keys()) & set(vec2.keys())
        if not common_keys:
            return 0.0
        
        dot = sum(vec1[k] * vec2[k] for k in common_keys)
        norm1 = sum(v**2 for v in vec1.values()) ** 0.5
        norm2 = sum(v**2 for v in vec2.values()) ** 0.5
        
        if norm1 > 0 and norm2 > 0:
            return dot / (norm1 * norm2)
        return 0.0


tfidf = TFIDFEmbedder()


def load_embeddings():
    """Load or build embeddings for all vault notes."""
    global EMBEDDINGS, NOTE_VECTORS
    
    if EMBEDDINGS_FILE.exists():
        try:
            data = json.loads(EMBEDDINGS_FILE.read_text(encoding="utf-8"))
            if data.get("vault_path") == str(VAULT_PATH) and data.get("note_count", 0) > 0:
                EMBEDDINGS = {k: v for k, v in data.get("embeddings", {}).items()}
                
                if USE_SENTENCE_TRANSFORMERS:
                    for path, vec in EMBEDDINGS.items():
                        NOTE_VECTORS[path] = np.array(vec)
                
                print(f"[Embeddings] Loaded {len(EMBEDDINGS)} cached embeddings")
                return EMBEDDINGS
        except Exception as e:
            print(f"[Embeddings] Cache load error: {e}")
    
    build_embeddings()
    return EMBEDDINGS


def build_embeddings():
    """Build embeddings for all vault notes."""
    global EMBEDDINGS, NOTE_VECTORS
    EMBEDDINGS = {}
    NOTE_VECTORS = {}
    
    documents = []
    doc_paths = []
    
    for md_file in VAULT_PATH.rglob("*.md"):
        if md_file.name == "Welcome.md" or md_file.name.startswith("_"):
            continue
        
        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            title = md_file.stem.replace("_", " ").title()
            text = f"{title} {content[:1000]}"
            documents.append(text)
            doc_paths.append(str(md_file.relative_to(VAULT_PATH)))
        except Exception as e:
            print(f"[Embeddings] Error reading {md_file}: {e}")
            continue
    
    print(f"[Embeddings] Processing {len(documents)} documents...")
    
    if not documents:
        print("[Embeddings] No documents found to embed")
        return EMBEDDINGS
    
    if USE_SENTENCE_TRANSFORMERS:
        vectors = MODEL.encode(documents, show_progress_bar=False)
        for i, path in enumerate(doc_paths):
            EMBEDDINGS[path] = vectors[i].tolist()
            NOTE_VECTORS[path] = vectors[i]
    else:
        tfidf.fit(documents)
        for i, path in enumerate(doc_paths):
            vec = tfidf.transform(documents[i])
            NOTE_VECTORS[path] = vec
    
    _save_embeddings()
    print(f"[Embeddings] Indexed {len(EMBEDDINGS)} notes")
    return EMBEDDINGS


def _save_embeddings():
    """Save embeddings to disk."""
    data = {
        "vault_path": str(VAULT_PATH),
        "updated": datetime.now().isoformat(),
        "embeddings": EMBEDDINGS,
        "note_count": len(EMBEDDINGS)
    }
    with LOCK:
        EMBEDDINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def semantic_search(query, max_results=5):
    """Search vault using embeddings for semantic similarity."""
    if not EMBEDDINGS:
        load_embeddings()
    
    if not EMBEDDINGS:
        return []
    
    if USE_SENTENCE_TRANSFORMERS:
        query_vector = MODEL.encode([query])[0]
        similarities = []
        
        for path, vector in NOTE_VECTORS.items():
            sim = np.dot(query_vector, vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(vector)
            )
            similarities.append((path, float(sim)))
    else:
        query_vec = tfidf.transform(query)
        similarities = []
        
        for path, vec in NOTE_VECTORS.items():
            sim = tfidf.cosine_similarity(query_vec, vec)
            similarities.append((path, float(sim)))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:max_results]


def get_embedding(text):
    """Get embedding for arbitrary text."""
    if USE_SENTENCE_TRANSFORMERS:
        return MODEL.encode([text])[0].tolist()
    return tfidf.transform(text)


def find_similar_notes(note_path, max_results=3):
    """Find notes similar to a given note."""
    if note_path not in NOTE_VECTORS:
        return []
    
    target = NOTE_VECTORS[note_path]
    similarities = []
    
    if USE_SENTENCE_TRANSFORMERS:
        for path, vector in NOTE_VECTORS.items():
            if path == note_path:
                continue
            sim = np.dot(target, vector) / (
                np.linalg.norm(target) * np.linalg.norm(vector)
            )
            similarities.append((path, float(sim)))
    else:
        for path, vec in NOTE_VECTORS.items():
            if path == note_path:
                continue
            sim = tfidf.cosine_similarity(target, vec)
            similarities.append((path, float(sim)))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:max_results]


class EmbeddingSearch:
    """Embedding-based search integrated with Unified Layer."""
    
    def __init__(self):
        load_embeddings()
    
    def search(self, query, max_results=5):
        """Search vault semantically."""
        results = semantic_search(query, max_results)
        
        output = []
        for path, score in results:
            full_path = VAULT_PATH / path
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                title = full_path.stem.replace("_", " ").title()
                output.append({
                    "path": path,
                    "title": title,
                    "content": content[:500],
                    "score": round(score, 3)
                })
        
        return output
    
    def rebuild(self):
        """Rebuild embeddings (use after vault changes)."""
        build_embeddings()
    
    def get_stats(self):
        """Get embedding statistics."""
        return {
            "notes_indexed": len(EMBEDDINGS),
            "search_type": "semantic" if USE_SENTENCE_TRANSFORMERS else "tfidf",
            "model": "all-MiniLM-L6-v2" if USE_SENTENCE_TRANSFORMERS else "tfidf-fallback"
        }


def load_embedding_search():
    """Factory function."""
    return EmbeddingSearch()


if __name__ == "__main__":
    import sys
    sys.path.insert(0, r"str(Path(__file__).resolve().parent.parent)")
    
    search = load_embedding_search()
    
    print("=== Embedding Search ===")
    stats = search.get_stats()
    print(f"Notes indexed: {stats['notes_indexed']}")
    print(f"Search type: {stats['search_type']}")
    print(f"Model: {stats['model']}")
    
    print("\n=== Test: Semantic Search ===")
    queries = [
        "Python best practices for code optimization",
        "How to manage memory efficiently in AI",
        "Machine learning model compression techniques"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        results = search.search(query, max_results=2)
        for r in results:
            print(f"  [{r['score']:.3f}] {r['title']}")
            print(f"    {r['content'][:100]}...")
    
    print("\n=== Test: Similar Notes ===")
    from unified_layer import VaultIndex
    idx = VaultIndex()
    if idx.notes:
        first_note = list(idx.notes.keys())[0]
        similar = find_similar_notes(first_note, max_results=3)
        print(f"Notes similar to {first_note}:")
        for path, score in similar:
            print(f"  [{score:.3f}] {path}")
