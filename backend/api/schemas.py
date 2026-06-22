"""
Pydantic request/response models for the FastAPI API.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    """A single turn in the conversation (user message + assistant response)."""

    user: str
    assistant: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(5, ge=1, le=20)
    session_id: Optional[str] = Field(
        default=None,
        description="Pass null on first message; include returned session_id on follow-ups",
    )
    stream: bool = False
    # chat_history is now REMOVED — loaded from DB using session_id


class SourceDocument(BaseModel):
    source_file: str
    page: str | int
    score: float
    excerpt: str


class ContextWindowStats(BaseModel):
    original_count: int
    fitted_count: int
    dropped_count: int
    tokens_used: int
    tokens_budget: int
    utilization_pct: float
    overflow_prevented: bool


class ChatResponse(BaseModel):
    question: str
    condensed_question: str
    answer: str
    sources: List[SourceDocument]
    chunks_used: int
    latency_ms: float
    session_id: str  # Always returned — persist this in localStorage
    history_turns_used: int
    context_window: Optional[ContextWindowStats] = None


class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    last_active: str
    message_count: int
    turn_count: int


class SessionHistoryMessage(BaseModel):
    role: str
    content: str
    timestamp: str


class IngestResponse(BaseModel):
    status: str
    filename: str
    chunks_indexed: int
    message: str


class HealthResponse(BaseModel):
    status: str
    vector_store_count: int
    timestamp: str
    embedding_cache: Optional[dict] = None


class DocumentInfo(BaseModel):
    """Rich metadata for a single indexed document."""

    source_file: str
    file_type: str
    file_size_bytes: int
    file_size_display: str
    upload_timestamp: str
    chunk_count: int
    ingestion_id: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total_docs: int
    total_chunks: int
