# configs/settings.py
"""
Typed configuration loader using Pydantic.

Reads configs/config.yaml and exposes a validated AppConfig object.
Every module imports get_config() instead of reading YAML directly.

Usage:
    from configs.settings import get_config
    cfg = get_config()
    print(cfg.chunking.child_chunk_size)   # 128
    print(cfg.llm.model)                   # "llama3.2:3b"
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

import yaml
from loguru import logger
from pydantic import BaseModel, Field

# ── Sub-config models ─────────────────────────────────────────────────


class EmbeddingConfig(BaseModel):
    model_name: str = "BAAI/bge-base-en-v1.5"
    device: str = "mps"
    batch_size: int = 32
    cache_dir: str = "./models"
    use_cache: bool = True
    cache_directory: str = "./data/embedding_cache"
    cache_size_limit_gb: int = 2


class ChunkingConfig(BaseModel):
    strategy: str = "hierarchical"  # "flat" or "hierarchical"

    # Flat chunking
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Hierarchical chunking
    parent_chunk_size: int = 512
    parent_chunk_overlap: int = 32
    child_chunk_size: int = 128
    child_chunk_overlap: int = 16

    separators: List[str] = ["\n\n", "\n", ". ", " ", ""]


class VectorStoreConfig(BaseModel):
    provider: str = "chromadb"
    persist_directory: str = "./data/chroma_db"
    collection_name: str = "documind_store"
    distance_metric: str = "cosine"


class RetrievalConfig(BaseModel):
    strategy: str = "hybrid"  # "dense", "hybrid", or "parent"
    top_k: int = 5
    score_threshold: float = 0.3
    rerank: bool = True
    reranker_model: str = "BAAI/bge-reranker-base"
    reranker_candidates: int = 20
    dense_candidates: int = 20
    sparse_candidates: int = 20
    parent_candidates: int = 20


class LLMConfig(BaseModel):
    provider: str = "ollama"
    model: str = "llama3.2:3b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.1
    top_p: float = 0.9
    max_tokens: int = 1024
    streaming: bool = True
    warmup_on_start: bool = True
    num_ctx: int = 4096  # NEW


class ConversationConfig(BaseModel):
    max_history_turns: int = 5


class APIConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True


class EvaluationConfig(BaseModel):
    rag_model: str = "llama3.2:3b"
    judge_model: str = "mistral:7b"  # NEW: separate judge model
    dataset_path: str = "./evaluation/eval_dataset.json"
    results_path: str = "./evaluation/ragas_results.json"
    min_questions: int = 10
    timeout_seconds: int = 180  # Per-LLM-call timeout for RAGAS
    targets: dict = {
        "faithfulness": 0.80,
        "answer_relevancy": 0.80,
        "context_precision": 0.70,
        "context_recall": 0.70,
    }


class DocumentsConfig(BaseModel):
    registry_path: str = "./data/document_registry.json"


class AppConfig(BaseModel):
    """Root configuration object. Access any sub-config as an attribute."""

    embedding: EmbeddingConfig = EmbeddingConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    vector_store: VectorStoreConfig = VectorStoreConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    llm: LLMConfig = LLMConfig()
    conversation: ConversationConfig = ConversationConfig()
    api: APIConfig = APIConfig()
    evaluation: EvaluationConfig = EvaluationConfig()
    documents: DocumentsConfig = DocumentsConfig()


# ── Loader ───────────────────────────────────────────────────────────


def _find_config_path() -> Path:
    """Locate config.yaml starting from current working directory."""
    candidates = [
        Path("configs/config.yaml"),
        Path("../configs/config.yaml"),
        Path(__file__).parent / "config.yaml",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "config.yaml not found. Expected at configs/config.yaml "
        "relative to the project root."
    )


@lru_cache(maxsize=1)
def get_config(config_path: str = None) -> AppConfig:
    """
    Load and return the application config.

    Results are cached after the first call — call get_config.cache_clear()
    if you need to reload (e.g., during testing).

    Args:
        config_path: Optional explicit path. Auto-detected if None.

    Returns:
        Validated AppConfig instance.
    """
    from dotenv import load_dotenv

    load_dotenv()

    path = Path(config_path) if config_path else _find_config_path()

    with open(path) as f:
        raw = yaml.safe_load(f)

    if "OLLAMA_BASE_URL" in os.environ:
        raw.setdefault("llm", {})["base_url"] = os.environ["OLLAMA_BASE_URL"]

    if "OLLAMA_MODEL" in os.environ:
        raw.setdefault("llm", {})["model"] = os.environ["OLLAMA_MODEL"]

    if "EMBEDDING_DEVICE" in os.environ:
        raw.setdefault("embedding", {})["device"] = os.environ["EMBEDDING_DEVICE"]

    if "CHROMA_DB_DIR" in os.environ:
        raw.setdefault("vector_store", {})["persist_directory"] = os.environ[
            "CHROMA_DB_DIR"
        ]
    elif "DATA_DIR" in os.environ:
        raw.setdefault("vector_store", {})["persist_directory"] = os.path.join(
            os.environ["DATA_DIR"], "chroma_db"
        )

    config = AppConfig(**raw)
    logger.debug(f"Config loaded from '{path}'")
    return config
