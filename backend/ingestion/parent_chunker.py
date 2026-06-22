# ingestion/parent_chunker.py
"""
Hierarchical chunker for parent-document retrieval.

Produces two levels of chunks from each document:
  - Parent chunks: 512 tokens — what the LLM reads
  - Child chunks:  128 tokens — what gets embedded and searched

Only child chunks are stored in ChromaDB for vector search.
Parent text is stored as metadata on each child chunk (linked by parent_id).
"""

import uuid
from dataclasses import dataclass
from typing import List, Tuple

from configs.settings import get_config
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger


@dataclass
class HierarchicalChunk:
    """A child chunk with a reference to its parent text."""

    child_text: str
    parent_text: str
    parent_id: str
    child_index: int  # Position of this child within its parent
    source_file: str
    page: int | str
    extra_metadata: dict


class ParentDocumentChunker:
    """
    Splits documents into parent + child chunks for hierarchical retrieval.
    """

    def __init__(
        self,
        parent_chunk_size: int = None,
        parent_chunk_overlap: int = None,
        child_chunk_size: int = None,
        child_chunk_overlap: int = None,
    ):
        # Load from config if not explicitly overridden
        cfg = get_config().chunking
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_chunk_size or cfg.parent_chunk_size,
            chunk_overlap=parent_chunk_overlap or cfg.parent_chunk_overlap,
            separators=cfg.separators,
        )
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_chunk_size or cfg.child_chunk_size,
            chunk_overlap=child_chunk_overlap or cfg.child_chunk_overlap,
            separators=cfg.separators,
        )

    def split(self, documents: List[Document]) -> List[HierarchicalChunk]:
        """
        Split documents into hierarchical chunks.

        Returns a flat list of HierarchicalChunk objects.
        Each child chunk knows its parent's text and ID.
        """
        all_chunks: List[HierarchicalChunk] = []

        for doc in documents:
            source_file = doc.metadata.get("source", "unknown").split("/")[-1]
            page = doc.metadata.get("page", "?")

            # Split into parent chunks
            parent_docs = self.parent_splitter.create_documents(
                [doc.page_content], metadatas=[doc.metadata]
            )

            for parent_doc in parent_docs:
                parent_id = f"parent_{uuid.uuid4().hex[:12]}"
                parent_text = parent_doc.page_content

                # Split parent into child chunks
                child_docs = self.child_splitter.create_documents([parent_text])

                for child_idx, child_doc in enumerate(child_docs):
                    if len(child_doc.page_content.strip()) < 20:
                        continue  # Skip trivially short child chunks

                    all_chunks.append(
                        HierarchicalChunk(
                            child_text=child_doc.page_content,
                            parent_text=parent_text,
                            parent_id=parent_id,
                            child_index=child_idx,
                            source_file=source_file,
                            page=page,
                            extra_metadata={
                                k: v
                                for k, v in doc.metadata.items()
                                if k not in ("source", "page")
                            },
                        )
                    )

        logger.info(
            f"Hierarchical chunking: {len(documents)} docs → {len(all_chunks)} child chunks"
        )
        return all_chunks
