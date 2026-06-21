# retrieval/parent_retriever.py
"""
Parent-document retrieval: searches child chunks, returns parent text.

The child chunks (small) are stored in ChromaDB with parent_text in their metadata.
On retrieval, we find the best child chunks, then return their parent text to the LLM.
"""

from typing import List, Dict, Any
from loguru import logger

from ingestion.embedder import EmbeddingService
from retrieval.vector_store import VectorStore


class ParentRetriever:
    """
    Searches child chunk embeddings but returns parent chunk text.

    Produces denser, more contextual results than standard flat retrieval
    without sacrificing embedding precision.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: EmbeddingService,
    ):
        self.vector_store = vector_store
        self.embedder     = embedder

    def search(
        self,
        query: str,
        top_k: int = 5,
        candidates: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve by child chunk similarity, return parent chunk text.

        Args:
            query:      Natural language query
            top_k:      Number of results to return
            candidates: How many child chunks to retrieve before deduplication

        Returns:
            List of result dicts.
            'document' field contains PARENT text (longer, more context).
            'child_document' field contains the matched child text (for debugging).
        """
        query_vec = self.embedder.embed(query)
        child_hits = self.vector_store.search(query_vec, top_k=candidates)

        if not child_hits:
            return []

        # Deduplicate by parent_id — if two child chunks map to the same parent,
        # keep only the higher-scoring one
        seen_parents: Dict[str, Dict] = {}
        for hit in child_hits:
            parent_id   = hit["metadata"].get("parent_id")
            parent_text = hit["metadata"].get("parent_text")

            if not parent_id or not parent_text:
                # Chunk was ingested without parent metadata (old flat ingestion)
                # Fall back to using child text as document
                fallback_id = hit["id"]
                if fallback_id not in seen_parents or hit["score"] > seen_parents[fallback_id]["score"]:
                    seen_parents[fallback_id] = {
                        "id":              hit["id"],
                        "document":        hit["document"],   # child text as fallback
                        "child_document":  hit["document"],
                        "metadata":        hit["metadata"],
                        "score":           hit["score"],
                        "parent_id":       fallback_id,
                    }
                continue

            if parent_id not in seen_parents or hit["score"] > seen_parents[parent_id]["score"]:
                seen_parents[parent_id] = {
                    "id":              parent_id,
                    "document":        parent_text,           # LLM reads the parent
                    "child_document":  hit["document"],       # What was matched
                    "metadata":        hit["metadata"],
                    "score":           hit["score"],
                    "parent_id":       parent_id,
                }

        # Sort by child chunk score (best semantic match first) and return top_k
        results = sorted(seen_parents.values(), key=lambda x: x["score"], reverse=True)

        logger.debug(
            f"Parent retrieval: {len(child_hits)} child hits → "
            f"{len(seen_parents)} unique parents → top {top_k} returned"
        )

        return results[:top_k]
