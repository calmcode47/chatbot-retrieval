# retrieval/hybrid_retriever.py
"""
Hybrid retriever combining BM25 (sparse) and ChromaDB (dense) search.
Results merged using Reciprocal Rank Fusion (RRF).

The BM25 index is built from all documents currently in ChromaDB.
Call .rebuild_index() after ingesting new documents.

Usage:
    retriever = HybridRetriever(vector_store=store, embedder=embedder)
    results = retriever.search(query="What is the refund policy?", top_k=20)
"""

import math
from typing import List, Dict, Any

from rank_bm25 import BM25Okapi
from loguru import logger

from ingestion.embedder import EmbeddingService
from retrieval.vector_store import VectorStore


def _tokenize(text: str) -> List[str]:
    """
    Simple whitespace + lowercase tokenizer for BM25.
    Good enough for most English documents.
    """
    return text.lower().split()


def reciprocal_rank_fusion(
    dense_results: List[Dict],
    sparse_results: List[Dict],
    k: int = 60,
) -> List[Dict]:
    """
    Merge two ranked lists using Reciprocal Rank Fusion.

    RRF score for a document:
        score = sum over each list of: 1 / (rank + k)

    k=60 is the standard value from the original RRF paper.
    Higher k reduces the influence of top-ranked items.

    Returns a unified list sorted by combined RRF score, descending.
    """
    rrf_scores: Dict[str, float] = {}

    # Map from doc_id to the full result dict (for final output)
    doc_map: Dict[str, Dict] = {}

    # Score from dense ranking
    for rank, result in enumerate(dense_results, start=1):
        doc_id = result["id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (rank + k)
        doc_map[doc_id] = result

    # Score from sparse ranking
    for rank, result in enumerate(sparse_results, start=1):
        doc_id = result["id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (rank + k)
        doc_map[doc_id] = result

    # Sort by combined RRF score (descending)
    sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)

    fused = []
    for doc_id in sorted_ids:
        result = doc_map[doc_id].copy()
        result["rrf_score"] = rrf_scores[doc_id]
        fused.append(result)

    return fused


class HybridRetriever:
    """
    Combines ChromaDB dense retrieval with BM25 sparse retrieval.
    Merges results using Reciprocal Rank Fusion.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: EmbeddingService,
        dense_candidates: int = 20,
        sparse_candidates: int = 20,
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.dense_candidates = dense_candidates
        self.sparse_candidates = sparse_candidates

        # BM25 index — built from current ChromaDB contents
        self._bm25: BM25Okapi | None = None
        self._corpus_ids: List[str] = []
        self._corpus_docs: List[str] = []

        self.rebuild_index()

    def rebuild_index(self) -> None:
        """
        Fetch all documents from ChromaDB and build the BM25 index.
        Call this after ingesting new documents.
        """
        if self.vector_store.count == 0:
            logger.warning("Vector store is empty — BM25 index not built.")
            self._bm25 = None
            return

        logger.info("Building BM25 index from ChromaDB documents...")
        all_data = self.vector_store.collection.get(include=["documents"])

        self._corpus_ids  = all_data["ids"]
        self._corpus_docs = all_data["documents"]

        tokenized = [_tokenize(doc) for doc in self._corpus_docs]
        self._bm25 = BM25Okapi(tokenized)

        logger.success(f"BM25 index built: {len(self._corpus_ids)} documents indexed.")

    def _bm25_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Run BM25 keyword search. Returns top_k results as dicts."""
        if self._bm25 is None:
            return []

        query_tokens = _tokenize(query)
        scores = self._bm25.get_scores(query_tokens)

        # Get top_k indices by score
        indexed_scores = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for idx, score in indexed_scores:
            if score == 0.0:
                continue  # BM25 score of 0 = no keyword overlap at all
            results.append({
                "id":       self._corpus_ids[idx],
                "document": self._corpus_docs[idx],
                "score":    float(score),
                "metadata": {},   # BM25 doesn't store metadata — rehydrated below
                "source":   "bm25",
            })

        # Rehydrate metadata from ChromaDB for matched documents
        if results:
            ids_to_fetch = [r["id"] for r in results]
            meta_data = self.vector_store.collection.get(
                ids=ids_to_fetch, include=["metadatas"]
            )
            meta_map = dict(zip(meta_data["ids"], meta_data["metadatas"]))
            for r in results:
                r["metadata"] = meta_map.get(r["id"], {})

        return results

    def search(
        self,
        query: str,
        top_k: int = 5,
        where: dict = None,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search: dense + sparse, merged with RRF.

        Args:
            query:  Natural language query string
            top_k:  Number of final results to return
            where:  Optional ChromaDB metadata filter (applied to dense only)

        Returns:
            List of result dicts (same schema as VectorStore.search),
            sorted by RRF score.
        """
        # Dense retrieval via ChromaDB
        query_vec    = self.embedder.embed(query)
        dense_results = self.vector_store.search(
            query_vec,
            top_k=self.dense_candidates,
            where=where,
        )
        for r in dense_results:
            r["source"] = "dense"

        # Sparse retrieval via BM25
        sparse_results = self._bm25_search(query, top_k=self.sparse_candidates)

        # Merge with RRF
        fused = reciprocal_rank_fusion(dense_results, sparse_results)

        logger.debug(
            f"Hybrid search: {len(dense_results)} dense + "
            f"{len(sparse_results)} sparse → {len(fused)} fused → top {top_k} returned"
        )

        return fused[:top_k]
