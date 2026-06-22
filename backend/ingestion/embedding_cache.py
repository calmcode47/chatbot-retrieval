# ingestion/embedding_cache.py
"""
Persistent embedding cache using diskcache (file-based, no server required).

Key:   sha256(model_name + "::" + text) — hex string
Value: numpy float32 array serialized as raw bytes

The cache directory (data/embedding_cache/) persists across process restarts
and works inside Docker when mounted as a volume.

Usage:
    from ingestion.embedding_cache import EmbeddingCache
    cache = EmbeddingCache()
    vec = cache.get(text, model_name)    # None on miss
    cache.set(text, model_name, vec)
"""

import hashlib
import io
from pathlib import Path
from typing import List, Optional

import diskcache
import numpy as np
from loguru import logger


class EmbeddingCache:
    """
    Thread-safe, persistent embedding vector cache.

    Stores: hash(text + model_name) → float32 vector (numpy bytes)
    Tracks: hits, misses per session for reporting.
    """

    def __init__(self, cache_dir: str = "./data/embedding_cache"):
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        self._cache = diskcache.Cache(
            directory=cache_dir,
            size_limit=2 * 1024**3,  # 2 GB max disk usage
        )
        self._hits = 0
        self._misses = 0
        logger.info(
            f"EmbeddingCache initialized at '{cache_dir}'. "
            f"Entries: {len(self._cache):,}"
        )

    # ── Core API ──────────────────────────────────────────────────────

    def _key(self, text: str, model_name: str) -> str:
        """Deterministic cache key: sha256(model_name + "::" + text)."""
        content = f"{model_name}::{text}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, text: str, model_name: str) -> Optional[List[float]]:
        """
        Retrieve a cached embedding.

        Returns the embedding as List[float] on hit, or None on miss.
        """
        key = self._key(text, model_name)
        data = self._cache.get(key)

        if data is None:
            self._misses += 1
            return None

        # Deserialize numpy bytes → list
        arr = np.load(io.BytesIO(data))
        self._hits += 1
        return arr.tolist()

    def set(self, text: str, model_name: str, embedding: List[float]) -> None:
        """Store an embedding vector in the cache."""
        key = self._key(text, model_name)
        arr = np.array(embedding, dtype=np.float32)
        buf = io.BytesIO()
        np.save(buf, arr)
        self._cache.set(key, buf.getvalue())

    def set_batch(
        self,
        texts: List[str],
        model_name: str,
        embeddings: List[List[float]],
    ) -> None:
        """Cache a batch of (text, embedding) pairs."""
        for text, embedding in zip(texts, embeddings):
            self.set(text, model_name, embedding)

    def get_batch(
        self,
        texts: List[str],
        model_name: str,
    ) -> tuple[List[Optional[List[float]]], List[int], List[int]]:
        """
        Batch cache lookup.

        Returns:
            results:    List where each element is either a cached vector or None
            hit_indices:  Indices of texts that were cache hits
            miss_indices: Indices of texts that need to be computed
        """
        results = []
        hit_indices = []
        miss_indices = []

        for i, text in enumerate(texts):
            vec = self.get(text, model_name)
            results.append(vec)
            if vec is not None:
                hit_indices.append(i)
            else:
                miss_indices.append(i)

        return results, hit_indices, miss_indices

    # ── Stats & management ────────────────────────────────────────────

    @property
    def total_entries(self) -> int:
        return len(self._cache)

    @property
    def session_hits(self) -> int:
        return self._hits

    @property
    def session_misses(self) -> int:
        return self._misses

    @property
    def session_hit_rate(self) -> float:
        total = self._hits + self._misses
        return round(self._hits / total, 4) if total > 0 else 0.0

    @property
    def disk_size_mb(self) -> float:
        """Approximate disk usage in MB."""
        try:
            return round(self._cache.volume() / (1024**2), 2)
        except Exception:
            return 0.0

    def stats(self) -> dict:
        return {
            "total_cached_embeddings": self.total_entries,
            "session_hits": self.session_hits,
            "session_misses": self.session_misses,
            "session_hit_rate": self.session_hit_rate,
            "disk_size_mb": self.disk_size_mb,
        }

    def clear(self) -> int:
        """Wipe the entire cache. Returns number of entries deleted."""
        n = len(self._cache)
        self._cache.clear()
        logger.warning(f"Embedding cache cleared. {n:,} entries removed.")
        return n
