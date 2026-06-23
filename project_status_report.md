# DocuMind: Local RAG Q&A System
## Project Status Report — June 23, 2026

DocuMind is a private, local Retrieval-Augmented Generation (RAG) system designed to perform secure document question-answering. It is designed to run completely offline on local machines (leveraging Apple Silicon GPU acceleration) or containerized in the cloud.

---

## 1. Executive Summary

As of today, the system has progressed to support **fully self-contained, offline model execution**, removing external API/Ollama dependencies in production. We have successfully implemented:

1. **Self-Contained Local SLM**: Integrated a local Small Language Model (`Qwen/Qwen2.5-0.5B-Instruct`) that runs directly inside the Python backend process.
2. **Lazy Loading Wrapper Optimization**: Designed a custom `LazyChatHuggingFace` model wrapper that defers model loading until the first query is received, preventing startup memory crashes (OOM) on standard cloud servers.
3. **Cross-Platform Device Fallback**: Added automatic CPU/CUDA fallback when Apple MPS is requested but unavailable (e.g. on Linux cloud servers).
4. **Terminal Fine-Tuning Pipeline**: Provided a PyTorch training loop (`train_slm.py`) and standard chat formatted dataset (`train_dataset.json`) to train/fine-tune the local model directly in the terminal.
5. **Railway Cloud Deployment**: Fully containerized and deployed both services inside a single unified Railway project, resolving port expansions and startup connection issues.

---

## 2. Technical Architecture Overview

```mermaid
graph TD
    User([User])
    UI[React + Vite Frontend (Node.js Container)]
    API[FastAPI Backend (Python Container)]
    
    subgraph Ingestion Pipeline
        LD[Loaders: PDF/TXT/MD]
        subgraph Hierarchical Chunking
            PCK[Parent Chunker: 512-Token Parent Chunks]
            CCK[Child Chunker: 128-Token Child Chunks]
        end
        EMB[Embedder: BGE-Base-en-v1.5]
    end
    
    subgraph Storage & Indexing
        VS[(ChromaDB Vector Store)]
        BM25[BM25 Index - Sparse Search]
    end
    
    subgraph Retrieval & Generation
        HR[Hybrid Retriever: Dense + BM25]
        RRF[Reciprocal Rank Fusion - RRF]
        PR[Parent Retriever: Fetch parent text by child ID]
        CR[Cross-Encoder Reranker: BGE-Reranker-Base]
        CB[Context Builder]
        
        subgraph Local Python Inference
            SLM[LazyChatHuggingFace: Qwen2.5-0.5B]
        end
    end

    User -->|Upload / Chat| UI
    UI -->|REST API Calls| API
    API -->|Raw Doc| LD
    LD --> Hierarchical
    PCK --> CCK --> EMB -->|Vectors & Meta| VS
    CCK -->|Rebuild Sparse Index| BM25
    
    API -->|Query| HR
    HR -->|Dense Search| VS
    HR -->|Sparse Search| BM25
    VS & BM25 -->|Retrieve Candidates| RRF
    RRF -->|Ranked Child Chunks| PR
    PR -->|Fetch Parent Context| CR
    CR -->|Re-scored Parent Context| CB
    CB -->|Context String| SLM
    SLM -->|Factual Answer| API
    API -->|Response + Sources + Telemetry| UI
```

---

## 3. Implementation Status By Module

| Component | Target File | Status | Description |
| :--- | :--- | :--- | :--- |
| **Settings & Config** | [backend/configs/settings.py](file:///Users/mayank/chatbot-retrieval/backend/configs/settings.py), `backend/configs/config.yaml` | **Completed** | Typed configuration loader using Pydantic. Exposes configuration properties (chunk sizes, LLM names, hosts) to all components. |
| **Embeddings** | [backend/ingestion/embedder.py](file:///Users/mayank/chatbot-retrieval/backend/ingestion/embedder.py) | **Completed** | BAAI/bge-base-en-v1.5 wrapper with automatic GPU/CPU fallback mechanism optimized for container deployment. |
| **Vector Store** | [backend/retrieval/vector_store.py](file:///Users/mayank/chatbot-retrieval/backend/retrieval/vector_store.py) | **Completed** | Wrapped ChromaDB client persisting data to `backend/data/chroma_db` using cosine distance. |
| **Hybrid Retrieval** | [backend/retrieval/hybrid_retriever.py](file:///Users/mayank/chatbot-retrieval/backend/retrieval/hybrid_retriever.py) | **Completed** | Combines sparse (BM25Okapi) and dense (ChromaDB) retrieval using Reciprocal Rank Fusion (RRF, k=60) for improved keyword matching. |
| **Parent-Document Retrieval**| [backend/ingestion/parent_chunker.py](file:///Users/mayank/chatbot-retrieval/backend/ingestion/parent_chunker.py) | **Completed** | Splits documents into parent-child hierarchies. Retrieval matches the child chunks but returns the parent context to the LLM. |
| **LLM Interface** | [backend/generation/llm.py](file:///Users/mayank/chatbot-retrieval/backend/generation/llm.py) | **Completed** | Auto-selects Groq (cloud) if key is set, falls back to local HuggingFace SLM via `LazyChatHuggingFace` wrapper to run completely offline. |
| **FastAPI Backend** | [backend/api/main.py](file:///Users/mayank/chatbot-retrieval/backend/api/main.py) | **Completed** | REST endpoints for chat, delete, document ingestion, and health checks. Bypasses legacy Ollama warmups unless configured. |
| **Fine-Tuning Script** | [backend/scripts/train_slm.py](file:///Users/mayank/chatbot-retrieval/backend/scripts/train_slm.py) | **Completed** | PyTorch training loop executing on MPS/CUDA/CPU to fine-tune the local SLM on custom instruction datasets. |
| **Training Dataset** | [backend/data/train_dataset.json](file:///Users/mayank/chatbot-retrieval/backend/data/train_dataset.json) | **Completed** | ChatML formatted Q&A dataset containing base knowledge of the DocuMind RAG pipeline. |

---

## 4. Verification & Testing

### A. Railway Cloud Deployment
Both services build and deploy successfully under a unified project structure:
* **Backend API**: [https://documind-production-cd0f.up.railway.app](https://documind-production-cd0f.up.railway.app) (Status: **Online** / healthy `/api/v1/health` response).
* **Frontend Web App**: [https://documind-frontend-production-15cf.up.railway.app](https://documind-frontend-production-15cf.up.railway.app) (Status: **Online**).

### B. Local Training Pipeline
The training script was verified and successfully completed locally on your Mac's MPS GPU, achieving loss convergence and saving custom checkpoints:
```bash
2026-06-23 16:11:00.784 | INFO     | __main__:train:100 - Starting training loop...
2026-06-23 16:12:49.736 | INFO     | __main__:train:124 - Epoch 1/3 Completed | Average Loss: 2.9650
2026-06-23 16:19:51.494 | INFO     | __main__:train:124 - Epoch 2/3 Completed | Average Loss: 0.5898
2026-06-23 16:25:15.713 | INFO     | __main__:train:124 - Epoch 3/3 Completed | Average Loss: 0.1492
2026-06-23 16:25:15.742 | INFO     | __main__:train:127 - Saving fine-tuned model checkpoint to: ./models/fine-tuned-slm...
2026-06-23 16:25:19.843 | SUCCESS  | __main__:train:131 - Training complete! Fine-tuned model saved successfully.
```

---

## 5. Next Steps & Configurations
* **Run Completely Locally**:
  * Start FastAPI: `cd backend && uvicorn api.main:app --port 8000 --reload`
  * Start React: `cd frontend && npm run dev`
* **Train Custom Data**:
  * Edit [train_dataset.json](file:///Users/mayank/chatbot-retrieval/backend/data/train_dataset.json) to add custom instruction samples.
  * Run training: `cd backend && python3 scripts/train_slm.py`
