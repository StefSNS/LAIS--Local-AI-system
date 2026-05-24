"""
Reranker API v1.0
Cross-encoder style reranking for RAG retrieval results.
Uses BM25 + keyword overlap scoring to re-rank chunks after initial retrieval.
Based on LocalAI reranker pattern.
"""

import math
import re
from collections import Counter
from typing import Optional


class BM25Reranker:
    """
    BM25-based reranker for RAG chunks.
    Re-ranks retrieval results using query-chunk relevance scoring.
    No ML dependencies. Pure statistical ranking.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._corpus_freq = {}
        self._corpus_size = 0
        self._avg_doc_len = 0.0

    def fit(self, documents: list[str]) -> None:
        """Build corpus statistics from documents."""
        self._corpus_size = len(documents)
        if self._corpus_size == 0:
            return

        doc_freq = Counter()
        total_length = 0

        for doc in documents:
            tokens = self._tokenize(doc)
            total_length += len(tokens)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freq[token] += 1

        self._corpus_freq = dict(doc_freq)
        self._avg_doc_len = total_length / self._corpus_size if self._corpus_size > 0 else 1.0

    def score(self, query: str, document: str) -> float:
        """Calculate BM25 score for a query-document pair."""
        if not query or not document:
            return 0.0

        query_tokens = self._tokenize(query)
        doc_tokens = self._tokenize(document)
        doc_len = len(doc_tokens)

        score = 0.0
        for token in query_tokens:
            df = self._corpus_freq.get(token, 0)
            idf = math.log(
                (self._corpus_size - df + 0.5) / (df + 0.5) + 1.0
            ) if self._corpus_size > 0 else 0.0

            tf = doc_tokens.count(token)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self._avg_doc_len))
            score += idf * (numerator / denominator) if denominator > 0 else 0

        return score

    def rerank(
        self,
        query: str,
        chunks: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Rerank chunks by query relevance.

        Args:
            query: Search query
            chunks: List of chunk dicts with 'content' key
            top_k: Number of results to return

        Returns:
            Reranked chunks with 'rerank_score' added
        """
        if not chunks:
            return []

        documents = [c.get("content", "") for c in chunks]
        self.fit(documents)

        scored = []
        for i, chunk in enumerate(chunks):
            bm25 = self.score(query, chunk.get("content", ""))
            keyword = self._keyword_overlap(query, chunk.get("content", ""))
            final = 0.7 * bm25 + 0.3 * keyword

            result = dict(chunk)
            result["rerank_score"] = round(final, 4)
            result["bm25_score"] = round(bm25, 4)
            result["keyword_score"] = round(keyword, 4)
            scored.append(result)

        scored.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r'\b[a-z]{2,}\b', text.lower())

    @staticmethod
    def _keyword_overlap(query: str, document: str) -> float:
        """Calculate keyword overlap ratio."""
        query_tokens = set(re.findall(r'\b[a-z]{3,}\b', query.lower()))
        doc_tokens = set(re.findall(r'\b[a-z]{3,}\b', document.lower()))
        if not query_tokens:
            return 0.0
        overlap = len(query_tokens & doc_tokens)
        return overlap / len(query_tokens)


class HybridReranker:
    """
    Hybrid reranker combining BM25 with:
    - Keyword overlap scoring
    - Header/title boost
    - Recency boost
    - Source authority weighting
    """

    def __init__(self):
        self.bm25 = BM25Reranker()

    def rerank(
        self,
        query: str,
        chunks: list[dict],
        top_k: int = 5,
        weights: Optional[dict] = None,
    ) -> list[dict]:
        """
        Rerank chunks with hybrid scoring.

        Args:
            query: Search query
            chunks: List of chunk dicts
            top_k: Results to return
            weights: Custom scoring weights
        """
        if not chunks:
            return []

        w = weights or {
            "bm25": 0.4,
            "keyword": 0.25,
            "header_boost": 0.15,
            "recency": 0.1,
            "source_authority": 0.1,
        }

        documents = [c.get("content", "") for c in chunks]
        self.bm25.fit(documents)

        scored = []
        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "")

            bm25_score = self.bm25.score(query, content)
            keyword_score = BM25Reranker._keyword_overlap(query, content)
            header_score = self._header_boost(query, chunk)
            recency_score = self._recency_score(chunk)
            source_score = self._source_authority(chunk)

            final = (
                w["bm25"] * bm25_score +
                w["keyword"] * keyword_score +
                w["header_boost"] * header_score +
                w["recency"] * recency_score +
                w["source_authority"] * source_score
            )

            result = dict(chunk)
            result["rerank_score"] = round(final, 4)
            result["score_breakdown"] = {
                "bm25": round(bm25_score, 4),
                "keyword": round(keyword_score, 4),
                "header": round(header_score, 4),
                "recency": round(recency_score, 4),
                "source": round(source_score, 4),
            }
            scored.append(result)

        scored.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _header_boost(query: str, chunk: dict) -> float:
        header = chunk.get("header", "").lower()
        if not header:
            return 0.0
        query_tokens = set(BM25Reranker._tokenize(query))
        header_tokens = set(BM25Reranker._tokenize(header))
        overlap = len(query_tokens & header_tokens)
        return min(1.0, overlap * 0.5)

    @staticmethod
    def _recency_score(chunk: dict) -> float:
        created = chunk.get("created_at", "")
        if not created:
            return 0.3
        return 0.5

    @staticmethod
    def _source_authority(chunk: dict) -> float:
        source = chunk.get("source", "").lower()
        if any(x in source for x in ["research", "docs", "reference", "spec"]):
            return 1.0
        if any(x in source for x in ["notes", "memory", "journal"]):
            return 0.6
        return 0.4


_global_reranker: Optional[HybridReranker] = None


def get_reranker() -> HybridReranker:
    global _global_reranker
    if _global_reranker is None:
        _global_reranker = HybridReranker()
    return _global_reranker
