"""
RAG Pipeline v1.0 - Retrieval-Augmented Generation
Chunks vault documents, generates embeddings, retrieves relevant context,
and injects into LLM prompts. CPU-optimized for 3GB RAM constraint.
"""

import hashlib
import json
import math
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from threading import Lock


VAULT_PATH = Path(os.environ.get("OMNIS_VAULT_PATH", r"%USERPROFILE%\Desktop\AI projects\Obsidian\Unified Brain"))
RAG_CACHE_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "rag_cache"
RAG_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class TextChunker:
    """Splits documents into semantic chunks with overlap."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, source: str = "") -> list[dict]:
        """Split text into overlapping chunks."""
        paragraphs = self._split_by_paragraphs(text)
        chunks = []
        current_chunk = ""
        current_start = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunks.append(self._make_chunk(current_chunk, source, current_start))
                overlap_words = self._get_overlap(current_chunk)
                current_chunk = overlap_words + para
                current_start = len(current_chunk) - len(para)
            else:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += para

        if current_chunk:
            chunks.append(self._make_chunk(current_chunk, source, current_start))

        return chunks

    def chunk_markdown(self, filepath: Path) -> list[dict]:
        """Chunk a markdown file, respecting headers as natural boundaries."""
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        sections = self._split_by_headers(content)
        all_chunks = []

        for section in sections:
            if len(section["content"].strip()) < 50:
                continue
            chunks = self.chunk_text(section["content"], source=str(filepath))
            for chunk in chunks:
                chunk["header"] = section["header"]
                all_chunks.append(chunk)

        return all_chunks

    def _split_by_paragraphs(self, text: str) -> list[str]:
        return [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]

    def _split_by_headers(self, text: str) -> list[dict]:
        pattern = r'^(#{1,6})\s+(.+?)$'
        sections = []
        current_header = ""
        current_content = []

        for line in text.split("\n"):
            match = re.match(pattern, line)
            if match:
                if current_content:
                    sections.append({
                        "header": current_header,
                        "content": "\n".join(current_content),
                    })
                current_header = match.group(2).strip()
                current_content = [line]
            else:
                current_content.append(line)

        if current_content:
            sections.append({
                "header": current_header,
                "content": "\n".join(current_content),
            })

        return sections

    def _get_overlap(self, text: str) -> str:
        words = text.split()
        overlap_count = min(len(words), self.chunk_overlap // 5)
        return " ".join(words[-overlap_count:]) + "\n\n" if overlap_count else ""

    def _make_chunk(self, content: str, source: str, position: int) -> dict:
        chunk_id = hashlib.md5(f"{source}:{position}:{content[:50]}".encode()).hexdigest()[:12]
        return {
            "id": f"chunk_{chunk_id}",
            "content": content,
            "source": source,
            "position": position,
            "word_count": len(content.split()),
            "created_at": datetime.now().isoformat(),
        }


class EmbeddingEngine:
    """Lightweight embedding engine using TF-IDF + dimensionality reduction.
    No ML dependencies. Works entirely on CPU with minimal RAM.
    """

    def __init__(self, max_features: int = 500):
        self.max_features = max_features
        self.vocabulary = {}
        self.idf = {}
        self._doc_count = 0
        self._lock = Lock()

    def fit(self, documents: list[str]) -> None:
        """Build vocabulary and IDF from documents."""
        self._doc_count = len(documents)
        doc_freq = {}

        for doc in documents:
            tokens = self._tokenize(doc)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1

        sorted_terms = sorted(doc_freq.keys(), key=lambda x: doc_freq[x], reverse=True)
        self.vocabulary = {term: i for i, term in enumerate(sorted_terms[:self.max_features])}

        for term, df in doc_freq.items():
            if term in self.vocabulary:
                self.idf[term] = math.log((1 + self._doc_count) / (1 + df)) + 1

    def embed(self, text: str) -> list[float]:
        """Generate TF-IDF embedding vector."""
        tokens = self._tokenize(text)
        term_freq = {}
        for token in tokens:
            term_freq[token] = term_freq.get(token, 0) + 1

        max_freq = max(term_freq.values()) if term_freq else 1

        vector = [0.0] * len(self.vocabulary)
        for term, idx in self.vocabulary.items():
            if term in term_freq:
                tf = 0.5 + 0.5 * (term_freq[term] / max_freq)
                idf = self.idf.get(term, 1.0)
                vector[idx] = tf * idf

        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""
        return [self.embed(t) for t in texts]

    def save(self, filepath: Path) -> None:
        data = {
            "vocabulary": self.vocabulary,
            "idf": self.idf,
            "doc_count": self._doc_count,
            "max_features": self.max_features,
        }
        filepath.write_text(json.dumps(data), encoding="utf-8")

    def load(self, filepath: Path) -> bool:
        if not filepath.exists():
            return False
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            self.vocabulary = data["vocabulary"]
            self.idf = data["idf"]
            self._doc_count = data["doc_count"]
            self.max_features = data["max_features"]
            return True
        except Exception:
            return False

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        tokens = re.findall(r'\b[a-z]{3,}\b', text.lower())
        stop_words = {"the", "and", "for", "are", "but", "not", "you", "all",
                      "can", "had", "her", "was", "one", "our", "out", "has",
                      "have", "been", "this", "that", "from", "they", "will",
                      "each", "make", "like", "just", "over", "such", "more",
                      "than", "them", "very", "when", "come", "could", "would"}
        return [t for t in tokens if t not in stop_words]


class VectorStore:
    """Simple vector store with cosine similarity search."""

    def __init__(self, cache_path: Path = RAG_CACHE_DIR):
        self.cache_path = cache_path
        self.chunks = []
        self.vectors = []
        self._lock = Lock()

    def add_chunks(self, chunks: list[dict], vectors: list[list[float]]) -> None:
        with self._lock:
            existing_ids = {c["id"] for c in self.chunks}
            for chunk, vector in zip(chunks, vectors):
                if chunk["id"] not in existing_ids:
                    self.chunks.append(chunk)
                    self.vectors.append(vector)
                    existing_ids.add(chunk["id"])

    def search(self, query_vector: list[float], top_k: int = 5, min_score: float = 0.1) -> list[dict]:
        """Search for most similar chunks using cosine similarity."""
        if not self.vectors:
            return []

        scores = []
        for i, vector in enumerate(self.vectors):
            score = self._cosine_similarity(query_vector, vector)
            if score >= min_score:
                scores.append((score, i))

        scores.sort(reverse=True)
        results = []
        for score, idx in scores[:top_k]:
            chunk = dict(self.chunks[idx])
            chunk["relevance_score"] = round(score, 4)
            results.append(chunk)

        return results

    def get_stats(self) -> dict:
        return {
            "total_chunks": len(self.chunks),
            "vector_dim": len(self.vectors[0]) if self.vectors else 0,
        }

    def save(self) -> None:
        filepath = self.cache_path / "vectors.json"
        data = {"chunks": self.chunks, "vectors": self.vectors}
        filepath.write_text(json.dumps(data), encoding="utf-8")

    def load(self) -> bool:
        filepath = self.cache_path / "vectors.json"
        if not filepath.exists():
            return False
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            self.chunks = data["chunks"]
            self.vectors = data["vectors"]
            return True
        except Exception:
            return False

    def clear(self) -> None:
        with self._lock:
            self.chunks.clear()
            self.vectors.clear()

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class RAGPipeline:
    """
    Complete RAG pipeline: chunk â†’ embed â†’ store â†’ retrieve â†’ format context.
    """

    def __init__(self, vault_path: Path = VAULT_PATH):
        self.vault_path = vault_path
        self.chunker = TextChunker(chunk_size=500, chunk_overlap=100)
        self.embedding_engine = EmbeddingEngine(max_features=500)
        self.vector_store = VectorStore()
        self._indexed_files = set()
        self._last_indexed = None

        embedding_path = RAG_CACHE_DIR / "embeddings.json"
        if self.embedding_engine.load(embedding_path):
            self.vector_store.load()
            print(f"[RAG] Loaded cache: {self.vector_store.get_stats()['total_chunks']} chunks")

    def index_vault(self, force: bool = False) -> dict:
        """Index all markdown files in the vault."""
        start_time = time.time()
        new_chunks = 0
        files_processed = 0

        md_files = list(self.vault_path.rglob("*.md"))
        all_text = []
        all_chunks = []

        for filepath in md_files:
            if filepath.name == "Welcome.md":
                continue
            if str(filepath) in self._indexed_files and not force:
                continue

            try:
                chunks = self.chunker.chunk_markdown(filepath)
                if chunks:
                    all_chunks.extend(chunks)
                    all_text.extend([c["content"] for c in chunks])
                    self._indexed_files.add(str(filepath))
                    files_processed += 1
            except Exception as e:
                print(f"[RAG] Failed to chunk {filepath}: {e}")

        if all_chunks:
            self.embedding_engine.fit(all_text)
            vectors = self.embedding_engine.embed_batch(all_text)
            self.vector_store.add_chunks(all_chunks, vectors)

            embedding_path = RAG_CACHE_DIR / "embeddings.json"
            self.embedding_engine.save(embedding_path)
            self.vector_store.save()

            new_chunks = len(all_chunks)

        elapsed = time.time() - start_time
        self._last_indexed = datetime.now().isoformat()

        return {
            "files_processed": files_processed,
            "chunks_created": new_chunks,
            "total_chunks": self.vector_store.get_stats()["total_chunks"],
            "elapsed_seconds": round(elapsed, 2),
        }

    def retrieve(self, query: str, top_k: int = 5, min_score: float = 0.1) -> list[dict]:
        """Retrieve relevant chunks for a query."""
        query_vector = self.embedding_engine.embed(query)
        return self.vector_store.search(query_vector, top_k=top_k, min_score=min_score)

    def format_context(self, query: str, top_k: int = 5) -> str:
        """Retrieve and format context for LLM injection."""
        chunks = self.retrieve(query, top_k=top_k)
        if not chunks:
            return ""

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = Path(chunk["source"]).name if chunk["source"] else "unknown"
            header = chunk.get("header", "")
            context_parts.append(
                f"[Source {i}] {source}"
                f"{' | ' + header if header else ''}\n"
                f"{chunk['content']}\n"
            )

        return "\n---\n".join(context_parts)

    def inject_context(self, prompt: str, top_k: int = 5) -> str:
        """Create a context-enhanced prompt."""
        context = self.format_context(prompt, top_k=top_k)
        if not context:
            return prompt

        return f"""You are a helpful assistant with access to the following relevant context from the knowledge vault. Use this information to provide accurate, well-informed responses.

<relevant_context>
{context}
</relevant_context>

User query: {prompt}

Respond based on the context provided. If the context doesn't contain relevant information, say so clearly."""

    def get_stats(self) -> dict:
        stats = self.vector_store.get_stats()
        stats["indexed_files"] = len(self._indexed_files)
        stats["last_indexed"] = self._last_indexed
        return stats

    def reindex(self) -> dict:
        """Force re-index of entire vault."""
        self.vector_store.clear()
        self._indexed_files.clear()
        self.embedding_engine = EmbeddingEngine(max_features=500)
        return self.index_vault(force=True)


_global_pipeline: Optional[RAGPipeline] = None
_pipeline_lock = Lock()


def load_rag_pipeline() -> RAGPipeline:
    global _global_pipeline
    if _global_pipeline is None:
        with _pipeline_lock:
            if _global_pipeline is None:
                _global_pipeline = RAGPipeline()
    return _global_pipeline
