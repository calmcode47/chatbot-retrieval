# DocuMind: Local RAG Q&A System

DocuMind is a 100% private, locally hosted Retrieval-Augmented Generation (RAG) system for secure question-answering over your documents. It runs entirely on your local machine to guarantee data privacy.

## Core Tech
* Backend: FastAPI, Python, LangChain, Pydantic
* Frontend: React, Vite, Three.js
* Vector Store: ChromaDB
* Inference Host: Ollama (llama3.2:3b for pipeline generation, mistral:7b for evaluations)

## Key Features
* Hybrid Search: Combines semantic vector search (ChromaDB) with keyword search (BM25) using Reciprocal Rank Fusion (RRF).
* Hierarchical Retrieval: Splits documents into parent/child chunks to provide the LLM with broader parent context when child matches are found.
* Cross-Encoder Reranking: Uses bge-reranker-base to refine and re-score retrieval results.
* Auto-Targeting: Automatically detects when queries mention specific uploaded files (like README.md) and applies precise metadata filters and adaptive thresholds to retrieve the correct context.

## Directory Layout

The workspace is organized into self-contained backend and frontend folders:

```
.
├── backend/
│   ├── api/             # FastAPI app routers, schemas, and lifespan logic
│   ├── configs/         # Pydantic settings model and config.yaml parameters
│   ├── ingestion/       # Document loaders, chunkers, and embedding caches
│   ├── retrieval/       # Vector store wrapper, hybrid retriever, and rerankers
│   ├── generation/      # Ollama local LLM initialization templates
│   ├── pipeline/        # Conversational RAG chain memory state orchestration
│   ├── evaluation/      # Ragas evaluation runner and synthetic dataset generator
│   ├── scripts/         # Ingestion scripts, ablation studies, and benchmarks
│   ├── tests/           # Full pytest verification suite
│   ├── data/            # Local SQLite caches, Chroma DB, and raw documents (ignored)
│   └── models/          # Persistent local model weights directory (ignored)
│
├── frontend/
│   ├── src/             # React SPA pages (Home, About, Dashboard) and components
│   ├── public/          # Static icons and assets
│   ├── package.json
│   └── vite.config.js   # Dev environment and API proxy targets
│
├── docker-compose.yml   # Multi-service container definitions
├── Makefile             # Convenient target recipes (make serve, make ui, make test, etc.)
└── README.md            # Root documentation file
```

## Setup and Installation

### Prerequisites
* Install Docker Desktop and ensure the daemon is running.
* Install Ollama on your host Mac and download the required models:
  ```bash
  ollama pull llama3.2:3b
  ollama pull mistral:7b
  ```

### Running with Docker Compose (Recommended)
This command builds and runs the entire stack inside containers:
```bash
docker compose up --build
```
* Frontend UI: Access at http://localhost:8501
* Backend API: Health check and docs available at http://localhost:8000/api/v1/health

### Running Locally for Development

1. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt -r backend/requirements-dev.txt
   ```

2. Start the Backend API Server:
   ```bash
   make serve
   ```

3. Start the Frontend UI Dev Server (in a separate terminal):
   ```bash
   make ui
   ```

4. Run the test suite:
   ```bash
   make test
   ```
