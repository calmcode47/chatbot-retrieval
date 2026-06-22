"""
FastAPI application factory.
"""

import shutil
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from api.schemas import (ChatRequest, ChatResponse, DocumentInfo,
                         DocumentListResponse, HealthResponse, IngestResponse,
                         SessionInfo)
from api.session_store import SessionStore
from configs.settings import get_config
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from ingestion.chunker import DocumentChunker
from ingestion.document_registry import DocumentRegistry
from ingestion.embedder import EmbeddingService
from ingestion.loaders import load_file
from loguru import logger
from pipeline.conversational_chain import ConversationalRAGChain
from retrieval.vector_store import VectorStore

# Global state — initialized once at startup
rag_chain: ConversationalRAGChain = None
embedder: EmbeddingService = None
store: VectorStore = None
chunker: DocumentChunker = None
registry: DocumentRegistry = None
session_store: SessionStore = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all components and pre-warm the LLM on startup."""
    global rag_chain, embedder, store, chunker, registry, session_store

    logger.info("Starting DocuMind API...")

    # Load configuration
    cfg = get_config()

    # Initialize components
    embedder = EmbeddingService(
        model_name=cfg.embedding.model_name, device=cfg.embedding.device
    )
    store = VectorStore()
    chunker = DocumentChunker()
    registry = DocumentRegistry()
    session_store = SessionStore(db_path="data/sessions.db")
    logger.info(f"SessionStore ready. Stats: {session_store.global_stats()}")
    # Sync registry with what's actually in the vector store
    registry.sync_with_store(store.list_sources())

    rag_chain = ConversationalRAGChain(
        embedder=embedder,
        vector_store=store,
        model_name=cfg.llm.model,
        top_k=cfg.retrieval.top_k,
        score_threshold=cfg.retrieval.score_threshold,
        use_reranker=cfg.retrieval.rerank,
        reranker_candidates=cfg.retrieval.reranker_candidates,
    )

    # ── Warmup the Ollama LLM ──────────────────────────────────
    # This forces Ollama to load model weights into RAM NOW,
    # so the first real user query does not bear the cold-start cost.
    logger.info(
        f"Warming up Ollama LLM... (loading model weights into RAM at {cfg.llm.base_url})"
    )
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            warmup_payload = {
                "model": cfg.llm.model,
                "prompt": "warmup",
                "stream": False,
                "options": {"num_predict": 1},  # Generate only 1 token — fast
            }
            response = await client.post(
                f"{cfg.llm.base_url}/api/generate",
                json=warmup_payload,
            )
            if response.status_code == 200:
                logger.success("Ollama warmup complete. Model is in RAM.")
            else:
                logger.warning(
                    f"Ollama warmup returned {response.status_code}. Check if 'ollama serve' is running."
                )
    except httpx.ConnectError:
        logger.error(
            f"Cannot reach Ollama at {cfg.llm.base_url}. Start it with: ollama serve"
        )
    # ─────────────────────────────────────────────────────────────────

    logger.success("DocuMind API ready. All components initialized.")
    yield

    logger.info("Shutting down DocuMind API.")


app = FastAPI(
    title="DocuMind API",
    description="Local RAG-based document Q&A system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    from datetime import datetime

    stats = {
        "status": "ok",
        "vector_store_count": store.count,
        "timestamp": datetime.now().isoformat(),
    }
    # Include cache stats if available
    if embedder and embedder._cache:
        stats["embedding_cache"] = embedder.cache_stats()
    return stats


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Answer a question using RAG. Manages conversation history server-side."""
    if store.count == 0:
        raise HTTPException(
            status_code=400, detail="No documents indexed. Upload documents first."
        )

    # Get or create a session for this conversation
    session_id = session_store.get_or_create_session(request.session_id)

    # Load conversation history from DB
    history = session_store.get_history(session_id, last_n_turns=5)

    start = time.time()
    result = rag_chain.query(
        question=request.question,
        chat_history=history,
    )
    latency_ms = (time.time() - start) * 1000

    # Persist this turn to the DB
    session_store.add_turn(
        session_id=session_id,
        user_message=request.question,
        assistant_message=result["answer"],
    )

    ctx_stats = None
    if result.get("context_window"):
        from backend.api.schemas import ContextWindowStats

        ctx_stats = ContextWindowStats(**result["context_window"])

    return ChatResponse(
        question=result["question"],
        condensed_question=result.get("condensed_question", result["question"]),
        answer=result["answer"],
        sources=result["sources"],
        chunks_used=result["chunks_used"],
        latency_ms=round(latency_ms, 2),
        session_id=session_id,
        history_turns_used=len(history),
        context_window=ctx_stats,
    )


@app.post("/api/v1/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    """Upload and index a document."""
    allowed_types = [".pdf", ".txt", ".md"]
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, detail=f"Unsupported file type. Allowed: {allowed_types}"
        )

    # Save uploaded file
    save_path = Path("data/raw") / file.filename
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Ingest
    documents = load_file(str(save_path))
    chunks = chunker.split(documents)
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="The uploaded document contains no readable text or is empty.",
        )

    texts = [c.page_content for c in chunks]
    metadatas = [{"source_file": file.filename, **c.metadata} for c in chunks]
    embeddings = embedder.embed_batch(texts)
    ids = [f"{file.filename}_{i}_{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]

    store.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    # Register in document registry
    registry.register(
        source_file=file.filename,
        file_path=str(save_path),
        chunk_count=len(chunks),
    )

    # Rebuild BM25 index so new documents are immediately searchable
    if hasattr(rag_chain, "retriever") and rag_chain.retriever is not None:
        rag_chain.retriever.rebuild_index()
        logger.info("BM25 index rebuilt after new document ingestion.")

    return IngestResponse(
        status="success",
        filename=file.filename,
        chunks_indexed=len(chunks),
        message=f"Successfully indexed {len(chunks)} chunks from '{file.filename}'.",
    )


@app.get("/api/v1/documents", response_model=DocumentListResponse)
async def list_documents():
    """Return all indexed documents with rich metadata."""
    entries = registry.list_all()

    # Fallback: if registry is empty but store has documents
    # (e.g., documents were ingested before this feature was added),
    # create minimal entries from what's in ChromaDB
    if not entries and store.count > 0:
        for source in store.list_sources():
            entries.append(
                {
                    "source_file": source,
                    "file_type": source.split(".")[-1] if "." in source else "unknown",
                    "file_size_bytes": 0,
                    "file_size_display": "unknown",
                    "upload_timestamp": "unknown",
                    "chunk_count": 0,
                    "ingestion_id": "legacy",
                }
            )

    return DocumentListResponse(
        documents=[DocumentInfo(**e) for e in entries],
        total_docs=len(entries),
        total_chunks=store.count,
    )


@app.delete("/api/v1/documents/{filename}")
async def delete_document(filename: str):
    """Remove a document and all its chunks from the vector store."""
    deleted = store.delete_by_source(filename)
    registry.remove(filename)
    return {"deleted_chunks": deleted, "filename": filename}


# backend/api/main.py — new session endpoints


@app.post("/api/v1/sessions", response_model=SessionInfo)
async def create_session():
    """Create a new conversation session. Returns the session_id."""
    sid = session_store.create_session()
    info = session_store.get_session_info(sid)
    return SessionInfo(**info)


@app.get("/api/v1/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get metadata for an existing session."""
    info = session_store.get_session_info(session_id)
    if not info:
        raise HTTPException(
            status_code=404, detail=f"Session '{session_id}' not found."
        )
    return SessionInfo(**info)


@app.get("/api/v1/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Return the full message history for a session."""
    if not session_store.session_exists(session_id):
        raise HTTPException(
            status_code=404, detail=f"Session '{session_id}' not found."
        )
    messages = session_store.get_full_history(session_id)
    return {
        "session_id": session_id,
        "messages": messages,
        "count": len(messages),
    }


@app.delete("/api/v1/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear all messages in a session (reset conversation without losing session_id)."""
    if not session_store.session_exists(session_id):
        raise HTTPException(
            status_code=404, detail=f"Session '{session_id}' not found."
        )
    deleted = session_store.clear_session(session_id)
    return {"session_id": session_id, "messages_deleted": deleted, "status": "cleared"}


@app.get("/api/v1/sessions")
async def list_sessions():
    """Global session store statistics."""
    return session_store.global_stats()
