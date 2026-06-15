"""
Cross-encoder re-ranker using BAAI/bge-reranker-base.

Improves retrieval precision by re-scoring bi-encoder candidates
using a cross-attention model that reads query and document together.

Usage:
    reranker = CrossEncoderReranker()
    top_chunks = reranker.rerank(query="...", results=store.search(..., top_k=20))
"""

from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
from loguru import logger


class CrossEncoderReranker:
    """
    Re-ranks retrieval results using a cross-encoder.
    
    Workflow:
        1. Bi-encoder retrieves top-20 candidates (fast, approximate)
        2. CrossEncoder scores each (query, chunk) pair jointly (slower, precise)
        3. Return top-k by cross-encoder score
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        logger.info(f"Loading cross-encoder reranker: '{model_name}'")
        self.model = CrossEncoder(model_name, max_length=512)
        logger.success("Cross-encoder reranker loaded.")

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Re-rank a list of retrieval results using the cross-encoder.

        Args:
            query:   The user's question (same string used for bi-encoder search)
            results: Output from VectorStore.search() — list of dicts with 'document' key
            top_k:   How many top results to return after reranking

        Returns:
            Top-k results sorted by cross-encoder score (descending).
            Each result dict gains a new key: 'rerank_score' (float).
        """
        if not results:
            return []

        # Build (query, document) pairs — cross-encoder reads both together
        pairs = [[query, result["document"]] for result in results]

        # Score all pairs in one batch forward pass
        logger.debug(f"Re-ranking {len(pairs)} candidates with cross-encoder...")
        scores = self.model.predict(pairs, show_progress_bar=False)

        # Attach rerank score to each result and sort descending
        for result, score in zip(results, scores):
            result["rerank_score"] = float(score)

        reranked = sorted(results, key=lambda x: x["rerank_score"], reverse=True)

        top = reranked[:top_k]
        logger.debug(
            f"Reranking complete. "
            f"Top score: {top[0]['rerank_score']:.3f} | "
            f"Bottom of top-{top_k}: {top[-1]['rerank_score']:.3f}"
        )
        return top
