# Dockerfile.api — DocuMind FastAPI backend
# Multi-stage: builder installs packages, runtime copies only what's needed

# ── Stage 1: Builder ─────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# PyTorch CPU-only inside Docker (MPS unavailable in VM)
# The container calls Ollama on the HOST for LLM — no MPS needed for inference
# Embedding model (sentence-transformers) runs on CPU in the container
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code only (data is mounted as a volume)
COPY ingestion/  ./ingestion/
COPY retrieval/  ./retrieval/
COPY generation/ ./generation/
COPY pipeline/   ./pipeline/
COPY api/        ./api/
COPY configs/    ./configs/
COPY evaluation/ ./evaluation/

RUN mkdir -p data/raw data/chroma_db models

RUN useradd -m -u 1001 documind && chown -R documind:documind /app
USER documind

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health').raise_for_status()"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
