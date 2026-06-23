# ingestion/embedder.py
"""
Embedding service with optional persistent cache.

Memory optimisations for cloud deployment (e.g. Railway 1 GB limit):
  - LAZY loading: the SentenceTransformer weights are NOT loaded at startup.
    They are loaded on the first embed() / embed_batch() call.
  - Set EMBEDDING_MODEL env var to override the model (e.g. BAAI/bge-small-en-v1.5
    uses ~130 MB vs ~440 MB for bge-base-en-v1.5).

Cache is ON by default. Set use_cache=False to disable (e.g., in unit tests).
"""

import os
import threading
from typing import List, Optional

from loguru import logger


class EmbeddingService:
    """
    Produces dense embeddings using a SentenceTransformer model.

    The model is loaded LAZILY on the first embed call to avoid OOM during
    startup in memory-constrained environments (e.g. Railway free tier).
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-base-en-v1.5",
        device: str = None,
        batch_size: int = 32,
        use_cache: bool = True,
        cache_dir: str = "./data/embedding_cache",
    ):
        # Allow env var override for the model (cloud-friendly smaller model)
        self.model_name = os.getenv("EMBEDDING_MODEL", model_name)
        self.device = device  # resolved lazily
        self.batch_size = batch_size
        self._model = None
        self._model_lock = threading.Lock()

        logger.info(
            f"EmbeddingService configured: model='{self.model_name}' "
            f"(lazy — will load on first use)"
        )

        # Cache setup
        self._cache = None
        if use_cache:
            from ingestion.embedding_cache import EmbeddingCache
            self._cache = EmbeddingCache(cache_dir=cache_dir)

    # ── Lazy model loader ──────────────────────────────────────────────

    def _resolve_device(self) -> str:
        """Pick best available device: mps > cuda > cpu."""
        import torch
        d = self.device
        if d == "mps" and not torch.backends.mps.is_available():
            logger.warning("MPS requested but not available — falling back to CPU.")
            d = None
        if d is None:
            if torch.cuda.is_available():
                d = "cuda"
            elif torch.backends.mps.is_available():
                d = "mps"
            else:
                d = "cpu"
        return d

    def _get_model(self):
        """Return the SentenceTransformer model, loading it on first call (thread-safe)."""
        if self._model is None:
            with self._model_lock:
                if self._model is None:  # double-checked locking
                    from sentence_transformers import SentenceTransformer
                    device = self._resolve_device()
                    self.device = device
                    logger.info(
                        f"Loading embedding model '{self.model_name}' on '{device}'..."
                    )
                    self._model = SentenceTransformer(self.model_name, device=device)
                    logger.success(
                        f"Embedding model ready. "
                        f"Dimension: {self._model.get_sentence_embedding_dimension()}"
                    )
        return self._model

    # ── Public interface ───────────────────────────────────────────────

    @property
    def model(self):
        """Backwards-compat alias so existing callers that reference .model still work."""
        return self._get_model()

    @property
    def dimension(self) -> int:
        return self._get_model().get_sentence_embedding_dimension()

    def embed(self, text: str) -> List[float]:
        """Embed a single string. Returns cached result if available."""
        if self._cache:
            cached = self._cache.get(text, self.model_name)
            if cached is not None:
                return cached

        prefixed = f"Represent this sentence for searching relevant passages: {text}"
        embedding = self._get_model().encode(
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
        cached_results, hit_idx, miss_idx = self._cache.get_batch(
            texts, self.model_name
        )

        if not miss_idx:
            logger.debug(f"embed_batch: {len(texts)} texts — 100% cache hit")
            return cached_results

        miss_texts = [texts[i] for i in miss_idx]
        logger.info(
            f"embed_batch: {len(texts)} texts — "
            f"{len(hit_idx)} cache hits, {len(miss_idx)} to compute"
        )
        computed = self._compute_batch(miss_texts)

        self._cache.set_batch(miss_texts, self.model_name, computed)

        for miss_position, computed_vec in zip(miss_idx, computed):
            cached_results[miss_position] = computed_vec

        return cached_results

    def _compute_batch(self, texts: List[str]) -> List[List[float]]:
        """Run the actual model inference on a batch of texts."""
        if not texts:
            return []
        embeddings = self._get_model().encode(
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
