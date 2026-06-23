"""
Retriever module that wraps vector search and cross-encoder re-ranking.
"""

import math
from typing import Any, Dict, List, Optional

from loguru import logger
from retrieval.vector_store import VectorStore
# NOTE: CrossEncoder is imported inside RerankerService.__init__ (not here)
# to avoid loading 500 MB of model weights at module import time.


class RerankerService:
    """
    Wraps a SentenceTransformers CrossEncoder to re-score and re-rank document chunks
    relative to a query.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-base", device: str = None):
        import torch
        from sentence_transformers import CrossEncoder
        if device is None:
            device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.device = device
        self.model_name = model_name

        logger.info(f"Loading reranker model '{model_name}' on device '{device}'...")
        self.model = CrossEncoder(model_name, device=device)
        logger.info("Reranker model loaded successfully.")

    def rerank(
        self, query: str, results: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Re-ranks a list of candidate results against the query.

        Args:
            query: The user's query string
            results: List of search results from VectorStore
            top_k: Number of top re-ranked results to return

        Returns:
            Re-ranked and truncated list of search results
        """
        if not results:
            return []

        # Form pairs of [query, document]
        pairs = [[query, r["document"]] for r in results]

        logger.info(
            f"Re-ranking {len(results)} candidates using '{self.model_name}'..."
        )
        logits = self.model.predict(pairs)

        # Map raw logits to [0, 1] range using sigmoid, updating score in results
        for r, logit in zip(results, logits):
            score = 1 / (1 + math.exp(-float(logit)))
            r["score"] = score
            r["logit"] = float(logit)

        # Sort descending by the new re-ranked score
        reranked = sorted(results, key=lambda x: x["score"], reverse=True)
        logger.info("Re-ranking complete.")

        return reranked[:top_k]
