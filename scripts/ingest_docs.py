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


def ingest_document(
    file_path: str,
    embedder: EmbeddingService,
    store: VectorStore,
    chunker: DocumentChunker = None,
    use_parent_chunks: bool = False,
) -> int:
    """Ingest a single document. Returns number of child chunks indexed."""

    from ingestion.loaders import load_file
    import uuid

    logger.info(f"Ingesting: {file_path} (hierarchical={use_parent_chunks})")
    documents = load_file(file_path)
    file_name = Path(file_path).name

    if use_parent_chunks:
        from ingestion.parent_chunker import ParentDocumentChunker

        p_chunker = ParentDocumentChunker(
            parent_chunk_size=512,
            child_chunk_size=128,
        )
        hier_chunks = p_chunker.split(documents)

        if not hier_chunks:
            logger.warning(f"No chunks from {file_path}")
            return 0

        texts = [c.child_text for c in hier_chunks]
        metadatas = [
            {
                "source_file":   c.source_file,
                "page":          c.page,
                "parent_id":     c.parent_id,
                "parent_text":   c.parent_text,     # Stored as metadata on each child
                "child_index":   c.child_index,
                **c.extra_metadata,
            }
            for c in hier_chunks
        ]

    else:
        # Original flat chunking (unchanged)
        from ingestion.chunker import DocumentChunker
        active_chunker = chunker or DocumentChunker()
        chunks = active_chunker.split(documents)
        texts = [c.page_content for c in chunks]
        metadatas = [{"source_file": file_name, **c.metadata} for c in chunks]

    embeddings = embedder.embed_batch(texts)
    ids = [f"{file_name}_{i}_{uuid.uuid4().hex[:8]}" for i in range(len(texts))]
    store.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    logger.success(f"Indexed {len(texts)} chunks from '{file_name}'")
    return len(texts)



def main():
    parser = argparse.ArgumentParser(description="Ingest documents into DocuMind vector store")
    parser.add_argument("--source-dir", default="data/raw/", help="Directory containing documents")
    parser.add_argument("--file", default=None, help="Single file to ingest")
    parser.add_argument("--parent-chunks", action="store_true", help="Use parent-document hierarchical chunking")
    args = parser.parse_args()

    # Initialize components
    embedder = EmbeddingService()
    store = VectorStore()
    chunker = DocumentChunker(chunk_size=512, chunk_overlap=64)

    if args.file:
        ingest_document(args.file, embedder, store, chunker, use_parent_chunks=args.parent_chunks)
    else:
        source_dir = Path(args.source_dir)
        files = list(source_dir.glob("**/*.pdf")) + list(source_dir.glob("**/*.txt"))

        if not files:
            logger.warning(f"No .pdf or .txt files found in '{source_dir}'")
            return

        total_chunks = 0
        for file_path in files:
            total_chunks += ingest_document(str(file_path), embedder, store, chunker, use_parent_chunks=args.parent_chunks)

        logger.success(f"Ingestion complete. Total chunks indexed: {total_chunks}")
        logger.info(f"Vector store now contains {store.count} chunks total.")


if __name__ == "__main__":
    main()
