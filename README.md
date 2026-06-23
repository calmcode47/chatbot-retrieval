# DocuMind — Private RAG Q&A System

> Ask questions across your documents. Run entirely offline on Apple Silicon (or in the cloud with Groq). No data leaves your machine.

[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-vector--store-orange)](https://www.trychroma.com)
[![Ollama](https://img.shields.io/badge/Ollama-local--LLM-black)](https://ollama.com)
[![Groq](https://img.shields.io/badge/Groq-cloud--LLM-f55036?logo=groq)](https://groq.com)

---

## ✨ Features

| Feature | Detail |
|---------|--------|
| **Hybrid Search** | Semantic vector search (ChromaDB) + BM25 keyword search fused via RRF |
| **Hierarchical Retrieval** | Parent/child chunks so the LLM gets full context around matches |
| **Cross-Encoder Reranking** | `bge-reranker-base` re-scores retrieved chunks for precision |
| **Auto-Targeting** | Detects file-specific queries and applies metadata filters automatically |
| **Multi-LLM Support** | Groq (cloud, free tier) → Ollama (local) → HuggingFace SLM fallback |
| **Live Status Indicator** | Navbar badge polls `/api/v1/health` every 15 s — real-time API status |
| **Fully Dockerised** | One-command spin-up with `docker compose up --build` |

---

## 🗂️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, Three.js, vanilla CSS |
| **Backend** | FastAPI, LangChain, Pydantic v2 |
| **Vector Store** | ChromaDB (cosine similarity) |
| **Embeddings** | `BAAI/bge-base-en-v1.5` (sentence-transformers) |
| **Reranker** | `BAAI/bge-reranker-base` |
| **LLM (cloud)** | Groq — `llama3-8b-8192` (free API key) |
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
│   ├── pipeline/        # Conversational RAG chain + memory
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
│   ├── entrypoint.sh    # Injects BACKEND_URL into nginx.conf at runtime
│   └── vite.config.js   # Dev proxy (Vite dev server only)
│
├── docker-compose.yml   # Multi-service stack definition
├── Makefile             # make serve | make ui | make test | make ingest
└── README.md
```

---

## 🚀 Quick Start

### Option A — Docker Compose (recommended)

**Prerequisites:**
- Docker Desktop running
- Ollama installed on host with the required model:
  ```bash
  ollama pull llama3.2:3b
  ```

```bash
# Clone and run
git clone https://github.com/your-username/chatbot-retrieval.git
cd chatbot-retrieval
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend UI | http://localhost:8501 |
| Backend API | http://localhost:8000/api/v1/health |
| API Docs | http://localhost:8000/docs |

> The Nginx container reads `BACKEND_URL` from `docker-compose.yml` and injects it into the Nginx config at startup — no Vite dev server is involved in Docker mode.

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
2. Groq's free tier gives you **14,400 req/day** with `llama3-8b-8192`.

**Local / Docker:**
```bash
# .env (backend root) or docker-compose.yml environment section:
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama3-8b-8192   # optional — this is the default
```

**Docker Compose override:**
```yaml
# docker-compose.yml → documind-api → environment
- GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
- GROQ_MODEL=llama3-8b-8192
```

### Using Ollama (local)
```bash
OLLAMA_BASE_URL=http://localhost:11434   # or http://host.docker.internal:11434 in Docker
OLLAMA_MODEL=llama3.2:3b
USE_OLLAMA=true
```

---

## ☁️ Railway Deployment

### How to add the Groq API key on Railway

Because Railway is a cloud environment (no local GPU / Ollama), you **must** use Groq for the LLM. Here's the exact process:

1. **Open your Railway project** → select the **backend service** (documind-api).
2. Go to the **Variables** tab (left sidebar).
3. Click **+ New Variable** and add:

   | Variable | Value |
   |----------|-------|
   | `GROQ_API_KEY` | `gsk_your_key_here` |
   | `GROQ_MODEL` | `llama3-8b-8192` |
   | `EMBEDDING_DEVICE` | `cpu` |

4. Railway auto-redeploys on variable save. Watch the **Logs** tab — you should see:
   ```
   Using Groq LLM: model=llama3-8b-8192
   ```
5. The **API ONLINE** badge in the top-right of the site will turn green once the backend is healthy.

> **Tip:** Do NOT set `USE_OLLAMA=true` on Railway — there is no Ollama server available there.

### Frontend env on Railway

The frontend service needs `BACKEND_URL` pointing to the backend Railway URL:

| Variable | Value |
|----------|-------|
| `BACKEND_URL` | `https://your-backend-service.up.railway.app` |
| `PORT` | `8501` |

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
| `GET` | `/api/v1/health` | Service health + vector count |
| `GET` | `/api/v1/documents` | List all ingested documents |
| `POST` | `/api/v1/documents/upload` | Upload & ingest a file |
| `DELETE` | `/api/v1/documents/{id}` | Remove a document |
| `POST` | `/api/v1/chat` | Send a question, get a streamed answer |
| `DELETE` | `/api/v1/chat/history` | Clear conversation memory |

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

## 📄 License

MIT — see [LICENSE](LICENSE).
