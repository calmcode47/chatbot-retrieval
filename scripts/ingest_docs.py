"""
CLI script to ingest documents into the vector store.
Usage: python scripts/ingest_docs.py --source-dir data/raw/
"""

import argparse
from pathlib import Path
from loguru import logger

from ingestion.loaders import load_file
from ingestion.chunker import DocumentChunker
from ingestion.embedder import EmbeddingService
from retrieval.vector_store import VectorStore
import uuid


def ingest_document(file_path: str, embedder: EmbeddingService, store: VectorStore, chunker: DocumentChunker) -> int:
    """Ingest a single document. Returns number of chunks indexed."""

    logger.info(f"Ingesting: {file_path}")

    # Step 1: Load
    documents = load_file(file_path)

    # Step 2: Chunk
    chunks = chunker.split(documents)

    if not chunks:
        logger.warning(f"No chunks produced from {file_path}")
        return 0

    # Step 3: Extract texts and metadata
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]

    # Ensure source_file is set
    file_name = Path(file_path).name
    for meta in metadatas:
        meta["source_file"] = file_name

    # Step 4: Embed
    embeddings = embedder.embed_batch(texts)

    # Step 5: Generate unique IDs (file_name + chunk_index)
    ids = [f"{file_name}_{i}_{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]

    # Step 6: Store
    store.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    logger.success(f"Indexed {len(chunks)} chunks from '{file_name}'")
    return len(chunks)


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into DocuMind vector store")
    parser.add_argument("--source-dir", default="data/raw/", help="Directory containing documents")
    parser.add_argument("--file", default=None, help="Single file to ingest")
    args = parser.parse_args()

    # Initialize components
    embedder = EmbeddingService()
    store = VectorStore()
    chunker = DocumentChunker(chunk_size=512, chunk_overlap=64)

    if args.file:
        ingest_document(args.file, embedder, store, chunker)
    else:
        source_dir = Path(args.source_dir)
        files = list(source_dir.glob("**/*.pdf")) + list(source_dir.glob("**/*.txt"))

        if not files:
            logger.warning(f"No .pdf or .txt files found in '{source_dir}'")
            return

        total_chunks = 0
        for file_path in files:
            total_chunks += ingest_document(str(file_path), embedder, store, chunker)

        logger.success(f"Ingestion complete. Total chunks indexed: {total_chunks}")
        logger.info(f"Vector store now contains {store.count} chunks total.")


if __name__ == "__main__":
    main()
