"""
Benchmark retrieval quality at different chunk sizes and top_k values.
Run after indexing real documents with: python scripts/benchmark_retrieval.py
"""

import time
from ingestion.embedder import EmbeddingService
from retrieval.vector_store import VectorStore

# These are test queries relevant to your indexed documents.
# Replace with questions that have known answers in your documents.
TEST_QUERIES = [
    "What is the refund policy?",
    "How do I contact customer support?",
    "What are the payment methods accepted?",
    # Add more queries matching your actual document content
]

def benchmark(top_k_values: list[int] = [3, 5, 10]):
    embedder = EmbeddingService()
    store = VectorStore()

    print(f"\nTotal chunks in store: {store.count}")
    print("=" * 60)

    for top_k in top_k_values:
        print(f"\n── top_k = {top_k} ──")
        for query in TEST_QUERIES:
            start = time.time()
            q_vec = embedder.embed(query)
            results = store.search(q_vec, top_k=top_k)
            elapsed = (time.time() - start) * 1000

            print(f"  Query: '{query[:50]}...'")
            print(f"  Retrieval time: {elapsed:.1f}ms")
            print(f"  Top score: {results[0]['score']:.3f}  |  Bottom score: {results[-1]['score']:.3f}")
            print(f"  Sources: {[r['metadata'].get('source_file', '?') for r in results]}")
            print()

if __name__ == "__main__":
    benchmark()
