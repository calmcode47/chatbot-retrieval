"""
FastAPI application factory.
"""

import time
import httpx
import yaml
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import shutil
from pathlib import Path

from api.schemas import ChatRequest, ChatResponse, IngestResponse, HealthResponse
from pipeline.conversational_chain import ConversationalRAGChain
from ingestion.embedder import EmbeddingService
from ingestion.loaders import load_file
from ingestion.chunker import DocumentChunker
from retrieval.vector_store import VectorStore
import uuid


# Global state — initialized once at startup
rag_chain: ConversationalRAGChain = None
embedder: EmbeddingService = None
store: VectorStore = None
chunker: DocumentChunker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all components and pre-warm the LLM on startup."""
    global rag_chain, embedder, store, chunker

    logger.info("Starting DocuMind API...")

    # Load configuration
    config = {}
    config_path = Path("configs/config.yaml")
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            logger.info("Configuration loaded from configs/config.yaml")

    retrieval_cfg = config.get("retrieval", {})
    top_k = retrieval_cfg.get("top_k", 5)
    score_threshold = retrieval_cfg.get("score_threshold", 0.3)
    rerank = retrieval_cfg.get("rerank", True)
    reranker_candidates = retrieval_cfg.get("reranker_candidates", 20)

    embedding_cfg = config.get("embedding", {})
    emb_model = embedding_cfg.get("model_name", "BAAI/bge-base-en-v1.5")
    emb_device = embedding_cfg.get("device", None)

    llm_cfg = config.get("llm", {})
    llm_model = llm_cfg.get("model", "llama3.2:3b")

    # Initialize components
    embedder = EmbeddingService(model_name=emb_model, device=emb_device)
    store = VectorStore()
    chunker = DocumentChunker()
    rag_chain = ConversationalRAGChain(
        embedder=embedder,
        vector_store=store,
        model_name=llm_model,
        top_k=top_k,
        score_threshold=score_threshold,
        use_reranker=rerank,
        reranker_candidates=reranker_candidates,
    )

    # ── Warmup the Ollama LLM ──────────────────────────────────
    # This forces Ollama to load model weights into RAM NOW,
    # so the first real user query does not bear the cold-start cost.
    logger.info("Warming up Ollama LLM... (loading model weights into RAM)")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            warmup_payload = {
                "model": "llama3.2:3b",      # Must match your config
                "prompt": "warmup",
                "stream": False,
                "options": {"num_predict": 1},  # Generate only 1 token — fast
            }
            response = await client.post(
                "http://localhost:11434/api/generate",
                json=warmup_payload,
            )
            if response.status_code == 200:
                logger.success("Ollama warmup complete. Model is in RAM.")
            else:
                logger.warning(f"Ollama warmup returned {response.status_code}. Check if 'ollama serve' is running.")
    except httpx.ConnectError:
        logger.error("Cannot reach Ollama at localhost:11434. Start it with: ollama serve")
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
    return HealthResponse(
        status="ok",
        vector_store_count=store.count,
        timestamp=datetime.now().isoformat(),
    )


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Answer a question using the RAG pipeline."""
    if store.count == 0:
        raise HTTPException(status_code=400, detail="No documents indexed. Upload documents first.")

    start = time.time()
    
    # Convert ChatTurn objects to (user, assistant) tuple list
    history_tuples = [(turn.user, turn.assistant) for turn in (request.chat_history or [])]

    result = rag_chain.query(
        question=request.question,
        chat_history=history_tuples,
    )
    
    latency_ms = (time.time() - start) * 1000

    return ChatResponse(
        question=result["question"],
        condensed_question=result.get("condensed_question", result["question"]),
        answer=result["answer"],
        sources=result["sources"],
        chunks_used=result["chunks_used"],
        latency_ms=round(latency_ms, 2),
        history_turns_used=result.get("history_turns_used", 0),
    )


@app.post("/api/v1/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    """Upload and index a document."""
    allowed_types = [".pdf", ".txt", ".md"]
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed_types}")

    # Save uploaded file
    save_path = Path("data/raw") / file.filename
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Ingest
    documents = load_file(str(save_path))
    chunks = chunker.split(documents)
    texts = [c.page_content for c in chunks]
    metadatas = [{"source_file": file.filename, **c.metadata} for c in chunks]
    embeddings = embedder.embed_batch(texts)
    ids = [f"{file.filename}_{i}_{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]

    store.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    return IngestResponse(
        status="success",
        filename=file.filename,
        chunks_indexed=len(chunks),
        message=f"Successfully indexed {len(chunks)} chunks from '{file.filename}'.",
    )


@app.get("/api/v1/documents")
async def list_documents():
    """List all indexed documents."""
    return {"documents": store.list_sources()}


@app.delete("/api/v1/documents/{filename}")
async def delete_document(filename: str):
    """Remove a document and all its chunks from the vector store."""
    deleted = store.delete_by_source(filename)
    return {"deleted_chunks": deleted, "filename": filename}
