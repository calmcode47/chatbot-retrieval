"""
Text splitting strategies.
Converts raw documents into smaller, overlapping chunks for retrieval.
"""

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import (RecursiveCharacterTextSplitter,
                                      SentenceTransformersTokenTextSplitter)
from loguru import logger


class DocumentChunker:
    """
    Splits documents into retrievable chunks.

    Uses RecursiveCharacterTextSplitter which tries to split on natural
    boundaries (paragraphs → sentences → words → characters) in that order.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,  # character-based; switch to tiktoken for token-based
        )

    def split(self, documents: List[Document]) -> List[Document]:
        """
        Split a list of documents into chunks.
        Preserves and enriches metadata on each chunk.
        """
        chunks = self.splitter.split_documents(documents)

        # Enrich metadata with chunk index per source
        source_counters: dict = {}
        for chunk in chunks:
            source = chunk.metadata.get("source", "unknown")
            if source not in source_counters:
                source_counters[source] = 0
            chunk.metadata["chunk_index"] = source_counters[source]
            chunk.metadata["source_file"] = (
                Path(source).name if source != "unknown" else "unknown"
            )
            source_counters[source] += 1

        logger.info(f"Split {len(documents)} documents → {len(chunks)} chunks")
        return chunks

    def split_texts(
        self, texts: List[str], metadatas: List[dict] = None
    ) -> List[Document]:
        """Split raw strings directly."""
        if metadatas is None:
            metadatas = [{}] * len(texts)
        return self.splitter.create_documents(texts, metadatas=metadatas)
