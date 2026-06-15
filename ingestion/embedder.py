"""
Embedding service using sentence-transformers.
Converts text → 768-dimensional vectors using BAAI/bge-base-en-v1.5.
"""

from typing import List
import torch
from sentence_transformers import SentenceTransformer
from loguru import logger


class EmbeddingService:
    """
    Wraps sentence-transformers to produce dense embeddings.
    Singleton-style: load the model once, reuse across the app.
    """

    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5", device: str = None):
        # Auto-detect device: prefer MPS (Apple Silicon) over CPU
        if device is None:
            device = "mps" if torch.backends.mps.is_available() else "cpu"

        self.device = device
        self.model_name = model_name

        logger.info(f"Loading embedding model '{model_name}' on device '{device}'...")
        self.model = SentenceTransformer(model_name, device=device)
        logger.info(f"Embedding model loaded. Dimension: {self.model.get_sentence_embedding_dimension()}")

    @property
    def dimension(self) -> int:
        """Return the dimensionality of the embedding vectors."""
        return self.model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> List[float]:
        """
        Embed a single string.
        Returns a list of floats (the embedding vector).
        """
        # BGE models work best with a query prefix for retrieval tasks
        prefixed = f"Represent this sentence for searching relevant passages: {text}"
        embedding = self.model.encode(prefixed, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Embed a list of strings efficiently using batched inference.
        Returns a list of embedding vectors.
        """
        logger.info(f"Embedding {len(texts)} chunks in batches of {batch_size}...")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        logger.info("Batch embedding complete.")
        return embeddings.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """LangChain-compatible interface (called by HuggingFaceEmbeddings internally)."""
        return self.embed_batch(texts)

    def embed_query(self, text: str) -> List[float]:
        """LangChain-compatible interface for query embedding."""
        return self.embed(text)


# Quick test — run this file directly to verify the model works
if __name__ == "__main__":
    service = EmbeddingService()
    test_texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is a subset of artificial intelligence.",
    ]
    vectors = service.embed_batch(test_texts)
    print(f"Embedded {len(vectors)} texts")
    print(f"Vector dimension: {len(vectors[0])}")
    print(f"First 5 values of first vector: {vectors[0][:5]}")
