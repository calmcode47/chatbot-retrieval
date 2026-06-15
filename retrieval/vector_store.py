"""
ChromaDB vector store interface.
Handles: creating collections, adding embeddings, similarity search, deletion.
"""

from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb import Collection
from loguru import logger


class VectorStore:
    """
    Thin wrapper around ChromaDB with a clean interface.
    Persists to disk so your index survives restarts.
    """

    def __init__(
        self,
        persist_directory: str = "./data/chroma_db",
        collection_name: str = "documind_store",
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Persistent client — data is saved to disk
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get or create the collection
        self.collection: Collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # cosine similarity metric
        )

        logger.info(
            f"VectorStore initialized. Collection '{collection_name}' "
            f"has {self.collection.count()} documents."
        )

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """
        Add a batch of chunks to the vector store.

        Args:
            ids: Unique string ID for each chunk
            embeddings: Pre-computed embedding vectors
            documents: Raw text of each chunk
            metadatas: Dict with source_file, page_number, chunk_index, etc.
        """
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Added {len(ids)} chunks to '{self.collection_name}'.")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        where: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Similarity search: find the top-k most similar chunks.

        Args:
            query_embedding: The embedded query vector
            top_k: How many results to return
            where: Optional metadata filter, e.g. {"source_file": "policy.pdf"}

        Returns:
            List of dicts with keys: id, document, metadata, distance
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        # Flatten and structure the results
        hits = []
        for i in range(len(results["ids"][0])):
            hits.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                # Convert cosine distance → similarity score (0–1, higher = better)
                "score": 1 - results["distances"][0][i],
            })

        return hits

    def delete_by_source(self, source_file: str) -> int:
        """
        Remove all chunks belonging to a specific source document.
        Returns number of chunks deleted.
        """
        results = self.collection.get(where={"source_file": source_file})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} chunks from '{source_file}'.")
            return len(results["ids"])
        return 0

    def list_sources(self) -> List[str]:
        """Return a list of all unique source documents in the store."""
        results = self.collection.get(include=["metadatas"])
        sources = list({m["source_file"] for m in results["metadatas"] if "source_file" in m})
        return sorted(sources)

    @property
    def count(self) -> int:
        """Total number of chunks stored."""
        return self.collection.count()


# Quick test
if __name__ == "__main__":
    from ingestion.embedder import EmbeddingService

    embedder = EmbeddingService()
    store = VectorStore()

    # Add test documents
    test_docs = [
        "The refund policy allows returns within 30 days.",
        "Our office is located in San Francisco, California.",
        "Machine learning models require training data.",
    ]
    test_embeddings = embedder.embed_batch(test_docs)
    test_ids = [f"test_{i}" for i in range(len(test_docs))]
    test_metadatas = [{"source_file": "test.txt", "chunk_index": i} for i in range(len(test_docs))]

    store.add(ids=test_ids, embeddings=test_embeddings, documents=test_docs, metadatas=test_metadatas)

    # Search
    query = "What is the return policy?"
    query_vec = embedder.embed(query)
    results = store.search(query_vec, top_k=2)

    print(f"\nQuery: '{query}'")
    print(f"Top results:")
    for r in results:
        print(f"  Score: {r['score']:.3f} | {r['document']}")
