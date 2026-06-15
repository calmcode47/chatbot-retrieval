"""
Pydantic request/response models for the FastAPI API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


from typing import List, Optional, Tuple

class ChatTurn(BaseModel):
    """A single turn in the conversation (user message + assistant response)."""
    user: str
    assistant: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: Optional[int] = Field(5, ge=1, le=20)
    chat_history: Optional[List[ChatTurn]] = Field(
        default=[],
        description="Previous conversation turns. Send [] for first message.",
    )
    stream: Optional[bool] = False


class SourceDocument(BaseModel):
    source_file: str
    page: str | int
    score: float
    excerpt: str


class ChatResponse(BaseModel):
    question: str
    condensed_question: str          # The standalone question actually sent to retriever
    answer: str
    sources: List[SourceDocument]
    chunks_used: int
    latency_ms: float
    history_turns_used: int


class IngestResponse(BaseModel):
    status: str
    filename: str
    chunks_indexed: int
    message: str


class DocumentInfo(BaseModel):
    source_file: str


class HealthResponse(BaseModel):
    status: str
    vector_store_count: int
    timestamp: str
