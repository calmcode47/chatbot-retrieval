# ingestion/embedder.py
"""
Embedding service with optional persistent cache.

Cache is ON by default. Set use_cache=False to disable (e.g., in unit tests).
"""

from typing import List, Optional

import torch
from sentence_transformers import SentenceTransformer
from loguru import logger


class EmbeddingService:
    """
    Produces dense embeddings using BAAI/bge-base-en-v1.5.
    Integrates a persistent disk cache to skip recomputing known vectors.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-base-en-v1.5",
        device: str = None,
        batch_size: int = 32,
        use_cache: bool = True,
        cache_dir: str = "./data/embedding_cache",
    ):
        if device is None:
            device = "mps" if torch.backends.mps.is_available() else "cpu"

        self.device      = device
        self.model_name  = model_name
        self.batch_size  = batch_size

        logger.info(f"Loading embedding model '{model_name}' on '{device}'...")
        self.model = SentenceTransformer(model_name, device=device)
        logger.success(
            f"Embedding model ready. "
            f"Dimension: {self.model.get_sentence_embedding_dimension()}"
        )

        # Cache setup
        self._cache = None
        if use_cache:
            from ingestion.embedding_cache import EmbeddingCache
            self._cache = EmbeddingCache(cache_dir=cache_dir)

    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> List[float]:
        """Embed a single string. Returns cached result if available."""
        if self._cache:
            cached = self._cache.get(text, self.model_name)
            if cached is not None:
                return cached

        prefixed   = f"Represent this sentence for searching relevant passages: {text}"
        embedding  = self.model.encode(
            prefixed,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        result = embedding.tolist()

        if self._cache:
            self._cache.set(text, self.model_name, result)

        return result

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts with cache-aware batching.

        Only uncached texts are sent to the model.
        Cached texts are retrieved from disk and merged back in order.
        """
        if not self._cache:
            return self._compute_batch(texts)

        # Partition into hits (cached) and misses (need compute)
        cached_results, hit_idx, miss_idx = self._cache.get_batch(texts, self.model_name)

        if not miss_idx:
            # All texts already cached
            logger.debug(f"embed_batch: {len(texts)} texts — 100% cache hit")
            return cached_results

        # Compute only the misses
        miss_texts = [texts[i] for i in miss_idx]
        logger.info(
            f"embed_batch: {len(texts)} texts — "
            f"{len(hit_idx)} cache hits, {len(miss_idx)} to compute"
        )
        computed = self._compute_batch(miss_texts)

        # Store computed embeddings in cache
        self._cache.set_batch(miss_texts, self.model_name, computed)

        # Merge: fill in computed results at miss positions
        for miss_position, computed_vec in zip(miss_idx, computed):
            cached_results[miss_position] = computed_vec

        return cached_results

    def _compute_batch(self, texts: List[str]) -> List[List[float]]:
        """Run the actual model inference on a batch of texts."""
        if not texts:
            return []
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 20,
        )
        return embeddings.tolist()

    def cache_stats(self) -> Optional[dict]:
        """Return cache statistics, or None if cache is disabled."""
        return self._cache.stats() if self._cache else None

    # LangChain-compatible interface
    def embed_query(self, text: str) -> List[float]:
        return self.embed(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embed_batch(texts)
