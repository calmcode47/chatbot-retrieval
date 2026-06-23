# DocuMind — Private RAG Q&A System

> Ask questions across your documents. Run entirely offline on Apple Silicon, or deploy to the cloud with Groq in minutes.

[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-vector--store-orange)](https://www.trychroma.com)
[![Ollama](https://img.shields.io/badge/Ollama-local--LLM-black)](https://ollama.com)
[![Groq](https://img.shields.io/badge/Groq-cloud--LLM-f55036?logo=groq)](https://groq.com)
[![Railway](https://img.shields.io/badge/Railway-deployed-6441a5?logo=railway)](https://railway.app)

🔗 **Live Demo:** [https://documind-frontend-production-15cf.up.railway.app](https://documind-frontend-production-15cf.up.railway.app)

---

## ✨ Features

| Feature | Detail |
|---------|--------|
| **Hybrid Search** | Semantic vector search (ChromaDB) + BM25 keyword search fused via Reciprocal Rank Fusion |
| **Hierarchical Retrieval** | Parent/child chunks so the LLM gets full context around each match |
| **Cross-Encoder Reranking** | `bge-reranker-base` re-scores retrieved chunks for precision (disabled on Railway to save RAM) |
| **Auto-Targeting** | Detects file-specific queries and applies metadata filters automatically |
| **Multi-LLM Support** | Groq (cloud, free tier) → Ollama (local) → HuggingFace SLM fallback |
| **Conversational Memory** | Server-side session store (SQLite) for multi-turn chat history |
| **Live Status Indicator** | Navbar badge polls `/api/v1/health` every 15 s — real-time API status |
| **Fully Dockerised** | One-command spin-up with `docker compose up --build` |

---

## 🗂️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, Three.js, vanilla CSS |
| **Backend** | FastAPI, LangChain, Pydantic v2 |
| **Vector Store** | ChromaDB (cosine similarity, HNSW) |
| **Embeddings** | `BAAI/bge-small-en-v1.5` on Railway · `BAAI/bge-base-en-v1.5` locally |
| **Reranker** | `BAAI/bge-reranker-base` (local only) |
| **LLM (cloud)** | Groq — `llama-3.1-8b-instant` (free API key) |
| **LLM (local)** | Ollama — `llama3.2:3b` |
| **LLM (fallback)** | `Qwen/Qwen2.5-0.5B-Instruct` via HuggingFace |

---

## 📁 Directory Layout

```
.
├── backend/
│   ├── api/             # FastAPI routers, schemas, lifespan hooks
│   ├── configs/         # Pydantic settings + config.yaml
│   ├── ingestion/       # Document loaders, chunkers, embedding cache
│   ├── retrieval/       # Hybrid retriever, vector store wrapper, rerankers
│   ├── generation/      # LLM init (Groq / Ollama / HuggingFace)
│   ├── pipeline/        # Conversational RAG chain + context window manager
│   ├── evaluation/      # Ragas runner + synthetic dataset generator
│   ├── scripts/         # Ingestion helpers, ablation studies, benchmarks
│   ├── tests/           # pytest suite
│   ├── data/            # ChromaDB, SQLite caches, raw docs  (git-ignored)
│   └── models/          # Local model weights                 (git-ignored)
│
├── frontend/
│   ├── src/             # React SPA — Home, Dashboard, About + components
│   ├── public/          # Static icons
│   ├── Dockerfile       # Multi-stage build → Nginx serving
│   ├── nginx.conf       # Reverse proxy config (50MB upload limit)
│   ├── entrypoint.sh    # Injects BACKEND_URL into nginx.conf at runtime
│   └── vite.config.js   # Dev proxy (Vite dev server only)
│
├── docker-compose.yml   # Multi-service stack definition
├── Makefile             # make serve | make ui | make test | make ingest
└── README.md
```

---

## 🚀 Quick Start

### Option A — Docker Compose (recommended for local)

**Prerequisites:**
- Docker Desktop running
- Ollama installed on host with the required model:
  ```bash
  ollama pull llama3.2:3b
  ```

```bash
# Clone and run
git clone https://github.com/calmcode47/chatbot-retrieval.git
cd chatbot-retrieval
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend UI | http://localhost:8501 |
| Backend API | http://localhost:8000/api/v1/health |
| API Docs | http://localhost:8000/docs |

> The Nginx container reads `BACKEND_URL` from `docker-compose.yml` and injects it into the Nginx config at startup.

---

### Option B — Local Development

```bash
# 1. Install Python deps
pip install -r backend/requirements.txt -r backend/requirements-dev.txt

# 2. Start backend (in terminal 1)
make serve

# 3. Start frontend dev server (in terminal 2)
make ui

# 4. Run test suite
make test
```

---

## 🔑 LLM Configuration

The backend checks env vars in this priority order:

```
GROQ_API_KEY set?  →  use Groq  (fastest, free, cloud)
USE_OLLAMA=true?   →  use Ollama (local, no internet)
otherwise          →  use Qwen2.5-0.5B via HuggingFace (fallback, slow)
```

### Using Groq (free cloud API — recommended for Railway)

1. Sign up at https://console.groq.com and create a free API key.
2. Groq's free tier gives you **14,400 req/day**.

**Local / Docker:**
```bash
# .env or docker-compose.yml environment section:
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.1-8b-instant   # recommended active model
```

### Using Ollama (local)
```bash
OLLAMA_BASE_URL=http://localhost:11434   # or http://host.docker.internal:11434 in Docker
OLLAMA_MODEL=llama3.2:3b
USE_OLLAMA=true
```

---

## ☁️ Railway Deployment

### Backend service variables

| Variable | Value | Notes |
|----------|-------|-------|
| `GROQ_API_KEY` | `gsk_your_key_here` | Required for cloud LLM |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Active Groq model (not deprecated) |
| `EMBEDDING_DEVICE` | `cpu` | No GPU on Railway |
| `SCORE_THRESHOLD` | `0.0` | Disables score filtering (RRF scores can be negative) |
| `OMP_NUM_THREADS` | `1` | Prevents CPU thrashing on shared Railway instances |

Railway auto-detects the `RAILWAY_ENVIRONMENT` variable and switches to a memory-efficient profile automatically:
- Uses `BAAI/bge-small-en-v1.5` (~130 MB) instead of `bge-base-en-v1.5` (~440 MB)
- Disables the cross-encoder reranker (~500 MB saved)

Watch the **Logs** tab — you should see:
```
Railway environment detected — switching to memory-efficient profile
Using Groq LLM: model=llama-3.1-8b-instant
DocuMind API ready. All components initialized.
```

> ⚠️ Do NOT set `USE_OLLAMA=true` on Railway — there is no Ollama server available there.

### Frontend service variables

| Variable | Value | Notes |
|----------|-------|-------|
| `BACKEND_URL` | `https://your-backend.up.railway.app` | **Must be the public HTTPS URL** |
| `PORT` | `8501` | Port Nginx listens on |

> ⚠️ Use the **public HTTPS URL** (not `http://documind:8080`). Railway's internal DNS can cause Nginx to cache stale IPs after backend redeploys, leading to 502/504 errors. The public URL routes through Railway's stable edge load balancer and avoids this problem.

---

## 🔍 Live Status Indicator

The Navbar displays a real-time API status badge:

| State | Color | Meaning |
|-------|-------|---------| 
| 🟡 **CONNECTING…** | Amber | Polling on startup |
| 🟢 **API ONLINE** | Green (pulsing) | Backend `/health` returned 200 |
| 🔴 **API OFFLINE** | Red | Backend unreachable or returned error |

The badge polls `/api/v1/health` every **15 seconds** automatically.

---

## 📊 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/v1/health` | Service health + vector store count |
| `GET`  | `/api/v1/documents` | List all ingested documents |
| `POST` | `/api/v1/ingest` | Upload & ingest a file (PDF, TXT, MD — up to 50 MB) |
| `DELETE` | `/api/v1/documents/{filename}` | Remove a document and its chunks |
| `POST` | `/api/v1/chat` | Send a question, get a RAG answer with sources |

---

## 🧪 Evaluation

DocuMind uses [Ragas](https://docs.ragas.io) for automated RAG evaluation:

```bash
make evaluate          # Run full eval suite
make generate-dataset  # Generate synthetic eval dataset
```

Target metrics:

| Metric | Target |
|--------|--------|
| Faithfulness | ≥ 0.80 |
| Answer Relevancy | ≥ 0.80 |
| Context Precision | ≥ 0.70 |
| Context Recall | ≥ 0.70 |

---

## ⚠️ Known Limitations

- **No persistence across Railway redeploys** — ChromaDB data is ephemeral on Railway's free tier. You'll need to re-upload documents after each backend restart. Add a Railway Volume for persistence.
- **Cold start latency** — The embedding model (`bge-small`) is loaded lazily on the first upload/query (~4 s on Railway free tier).
- **Groq rate limits** — Free tier: 14,400 req/day, 30 req/min. Use `llama-3.1-8b-instant` for best throughput.

---

## 📄 License

MIT — see [LICENSE](LICENSE).
