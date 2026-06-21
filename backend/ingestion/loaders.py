"""
Document loaders supporting PDF, TXT, and web URLs.
Returns a list of LangChain Document objects.
"""

from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    WebBaseLoader,
    DirectoryLoader,
)
from loguru import logger


def load_pdf(file_path: str) -> List[Document]:
    """Load a PDF file. Returns one Document per page."""
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()
    logger.info(f"Loaded PDF '{file_path}': {len(documents)} pages")
    return documents


def load_text(file_path: str) -> List[Document]:
    """Load a plain text file."""
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    logger.info(f"Loaded TXT '{file_path}': {len(documents)} documents")
    return documents


def load_url(url: str) -> List[Document]:
    """Load a web page, extracting its text content."""
    loader = WebBaseLoader(url)
    documents = loader.load()
    logger.info(f"Loaded URL '{url}': {len(documents)} documents")
    return documents


def load_directory(directory: str, glob: str = "**/*.pdf") -> List[Document]:
    """Load all matching files from a directory recursively."""
    loader = DirectoryLoader(directory, glob=glob, loader_cls=PyMuPDFLoader)
    documents = loader.load()
    logger.info(f"Loaded directory '{directory}': {len(documents)} documents")
    return documents


def load_file(file_path: str) -> List[Document]:
    """Dispatch to the correct loader based on file extension."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext in [".txt", ".md"]:
        return load_text(file_path)
    elif file_path.startswith("http"):
        return load_url(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: .pdf, .txt, .md, URLs")
