# DocuMind: Local RAG Q&A System
## Project Status Report — June 18, 2026

DocuMind is a 100% private, local Retrieval-Augmented Generation (RAG) system designed to perform secure document question-answering. It uses Apple Silicon GPU-acceleration (MPS) for embedding generation, ChromaDB for persistent vector search, and Ollama to host LLMs locally.

---

## 1. Executive Summary
As of today, the system has progressed to **Phase 13**, introducing advanced RAG techniques and structured, local evaluation. We have successfully implemented:
- **Hybrid Retrieval (BM25 + Dense Search)** with Reciprocal Rank Fusion (RRF).
- **Parent-Document Retrieval** featuring hierarchical chunking (512-token parent chunks / 128-token child chunks).
- **Local RAGAS Evaluation Runner** utilizing a synthetically generated grounded evaluation dataset.
As of today, the system has progressed to **Phase 15**, introducing containerized deployment, a dynamic configuration layer, and a state-of-the-art React frontend. We have successfully implemented:
- **Premium React + Vite Frontend**: Replaced the basic Streamlit UI with a beautiful, dark-themed Single Page Application featuring 3D particle constellation canvas backgrounds (via Three.js), a rotating wireframe hero centerpiece, interactive navigation, and real-time retrieval metrics (latencies, source-chunk citations, and confidence scores).
- **Dynamic Configuration System**: Centralized all ingestion, chunking, search, and LLM hyperparameters into `configs/config.yaml`, loaded dynamically via a validated Pydantic settings schema (`configs/settings.py`).
- **Full Docker Containerization**: Multi-container Docker composition (`documind-api` using Python 3.11-slim and `documind-ui` using Node.js 20-slim) configured to leverage the host's Apple Silicon GPU/MPS for local models.
- **Robust Local RAGAS Evaluation**: Upgraded `evaluation/ragas_eval.py` to use a separate model pipeline strategy (fast `llama3.2:3b` for pipeline answers, structured `mistral:7b` for JSON-based evaluation metrics) with 180-second timeouts, retry configurations, and dataset guards.

All pipeline processes are fully containerized and verified to compile and run successfully on localhost.

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
        OLL[Ollama on MacOS Host: Llama-3.2-3b]
    end

    User -->|Upload / Chat| UI
    UI -->|REST API Calls (VITE_API_BASE_URL)| API
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
    CB -->|Context String| OLL
    OLL -->|Factual Answer| API
    API -->|Response + Sources + Telemetry| UI
```

---

## 3. Implementation Status By Module

| Component | Target File | Status | Description |
| :--- | :--- | :--- | :--- |
| **Settings & Config** | [configs/settings.py](file:///Users/mayank/chatbot-retrieval/configs/settings.py), `configs/config.yaml` | **Completed** | Typed configuration loader using Pydantic. Exposes configuration properties (chunk sizes, LLM names, hosts) to all components. |
| **Embeddings** | [ingestion/embedder.py](file:///Users/mayank/chatbot-retrieval/ingestion/embedder.py) | **Completed** | BAAI/bge-base-en-v1.5 wrapper with automatic GPU/CPU fallback mechanism optimized for container deployment. |
| **Vector Store** | [retrieval/vector_store.py](file:///Users/mayank/chatbot-retrieval/retrieval/vector_store.py) | **Completed** | Wrapped ChromaDB client persisting data to `./data/chroma_db` using cosine distance. |
| **Hybrid Retrieval** | [retrieval/hybrid_retriever.py](file:///Users/mayank/chatbot-retrieval/retrieval/hybrid_retriever.py) | **Completed** | Combines sparse (BM25Okapi) and dense (ChromaDB) retrieval using Reciprocal Rank Fusion (RRF, $k=60$) for improved keyword matching. |
| **Parent-Document Retrieval**| [ingestion/parent_chunker.py](file:///Users/mayank/chatbot-retrieval/ingestion/parent_chunker.py), [retrieval/parent_retriever.py](file:///Users/mayank/chatbot-retrieval/retrieval/parent_retriever.py) | **Completed** | Splits documents into parent-child hierarchies. Retrieval matches the child chunks but returns the parent context to the LLM. |
| **Cross-Encoder Reranker** | [retrieval/reranker.py](file:///Users/mayank/chatbot-retrieval/retrieval/reranker.py) | **Completed** | Integrates `BAAI/bge-reranker-base` to re-score candidate chunks for increased context accuracy. |
| **Orchestrator** | [pipeline/conversational_chain.py](file:///Users/mayank/chatbot-retrieval/pipeline/conversational_chain.py) | **Completed** | Stateful multi-turn conversation memory, automatically condensing queries based on settings configurations. |
| **FastAPI Backend** | [api/main.py](file:///Users/mayank/chatbot-retrieval/api/main.py), [Dockerfile.api](file:///Users/mayank/chatbot-retrieval/Dockerfile.api) | **Completed** | REST endpoints for chat, delete, document ingestion, and health checks. Built as a containerized Python service listening on port `8000`. |
| **React Frontend UI** | [Dockerfile.ui](file:///Users/mayank/chatbot-retrieval/Dockerfile.ui), [ui/src/App.jsx](file:///Users/mayank/chatbot-retrieval/ui/src/App.jsx) | **Completed** | Premium React SPA built with Vite and served on port `8501`. Incorporates interactive 3D Three.js backgrounds, structured layout (Home, About, Dashboard), and complete telemetry/citations rendering. |
| **Embedding Cache** | [ingestion/embedding_cache.py](file:///Users/mayank/chatbot-retrieval/ingestion/embedding_cache.py) | **Completed** | Disk-based persistent embedding cache using `diskcache` to avoid redundant embedding generation and speed up ingestion. |
| **Document Registry** | [ingestion/document_registry.py](file:///Users/mayank/chatbot-retrieval/ingestion/document_registry.py) | **Completed** | Persistent JSON-based registry mapping indexed documents to rich metadata (size, file type, upload time, chunk count). |
| **RAGAS Evaluation** | [evaluation/ragas_eval.py](file:///Users/mayank/chatbot-retrieval/evaluation/ragas_eval.py) | **Completed** | Uses `llama3.2:3b` for pipeline generation and `mistral:7b` as LLM judge with 180s timeout, score validation, and dataset size guard. |

---

## 4. Verification & Testing

### A. Core Pipeline Verification
- **Container Deployments**: Both `documind-api` and `documind-ui` spin up and maintain healthy statuses:
  ```bash
  $ docker compose ps
  NAME           IMAGE                            STATUS                   PORTS
  documind-api   chatbot-retrieval-documind-api   Up 2 minutes (healthy)   0.0.0.0:8000->8000/tcp
  documind-ui    chatbot-retrieval-documind-ui    Up 2 minutes             0.0.0.0:8501->8501/tcp
  ```
- **RAG Chat Ingestion**: Interactive chat pipeline successfully resolves queries, displaying relevant parent context chunks, specific source file paths, and accurate latency metrics.

### B. Unit & Integration Testing
All unit tests pass successfully:
```bash
tests/test_retrieval.py::test_embedding_dimension PASSED                 [ 14%]
tests/test_retrieval.py::test_embedding_normalized PASSED                [ 28%]
tests/test_retrieval.py::test_vector_store_add_and_search PASSED         [ 42%]
tests/test_retrieval.py::test_context_builder PASSED                     [ 57%]
tests/test_retrieval.py::test_context_builder_empty PASSED               [ 71%]
tests/test_retrieval.py::test_reranker PASSED                            [ 85%]
tests/test_retrieval.py::test_conversational_chain_condense PASSED       [100%]
```

### C. Automated RAGAS Evaluation
By upgrading the LLM judge model to `mistral:7b` and setting the Ollama timeout to 180 seconds, evaluation queries execute reliably without timeout errors, yielding precise scores across all Ragas metrics (Faithfulness, Answer Relevancy, Context Precision, and Context Recall).

---

## 5. Roadmap & Future Improvements
1. **Ablation Studies**:
   - Utilize the configuration settings framework to execute evaluations across varying chunk sizes and reranker top-K values to optimize retrieval recall.
2. **Dynamic Context Windows**:
   - Programmatically adjust retriever limits based on length checks of retrieved contexts to prevent context window overflow on local LLMs.
3. **Advanced Session Memory**:
   - Extend conversational chain state to support database-backed message stores and user session management.
