# DocuMind: Local RAG Q&A System
## Project Status Report — June 21, 2026

DocuMind is a private, local Retrieval-Augmented Generation (RAG) system designed to perform secure document question-answering. It uses Apple Silicon GPU-acceleration (MPS) for embedding generation, ChromaDB for persistent vector search, and Ollama to host LLMs locally.

---

## 1. Executive Summary
As of today, the system has progressed to **Phase 16**, introducing backend-frontend code partitioning, Docker environment updates, and an optimized RAG query matching mechanism for target documents. We have successfully implemented:
* Codebase Partitioning: Restructured the workspace to separate frontend code (React + Vite) under a frontend directory and python processing pipelines (FastAPI, ingestion, retrieval, database, and configurations) under a backend directory.
* Docker Environment Reconfiguration: Realigned build contexts, volume mounts, and Dockerfiles to support the decoupled structure without breaking container operations.
* Optimized Target Document Querying: Configured a normalization layer that strips file extensions, spaces, and punctuation from both queries and registry source lists. When a specific target file is requested, the system automatically isolates search to the file's metadata and dynamically overrides similarity score thresholds.
* Unit Test Reconciliation: Re-established path mappings and PYTHONPATH environments so that all unit tests compile and run successfully inside the new backend layout.

All processes remain container-ready and verified to run successfully.

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
| **Settings & Config** | [backend/configs/settings.py](file:///Users/mayank/chatbot-retrieval/backend/configs/settings.py), `backend/configs/config.yaml` | **Completed** | Typed configuration loader using Pydantic. Exposes configuration properties (chunk sizes, LLM names, hosts) to all components. |
| **Embeddings** | [backend/ingestion/embedder.py](file:///Users/mayank/chatbot-retrieval/backend/ingestion/embedder.py) | **Completed** | BAAI/bge-base-en-v1.5 wrapper with automatic GPU/CPU fallback mechanism optimized for container deployment. |
| **Vector Store** | [backend/retrieval/vector_store.py](file:///Users/mayank/chatbot-retrieval/backend/retrieval/vector_store.py) | **Completed** | Wrapped ChromaDB client persisting data to `backend/data/chroma_db` using cosine distance. |
| **Hybrid Retrieval** | [backend/retrieval/hybrid_retriever.py](file:///Users/mayank/chatbot-retrieval/backend/retrieval/hybrid_retriever.py) | **Completed** | Combines sparse (BM25Okapi) and dense (ChromaDB) retrieval using Reciprocal Rank Fusion (RRF, k=60) for improved keyword matching. Filters BM25 results by file reference when targeted. |
| **Parent-Document Retrieval**| [backend/ingestion/parent_chunker.py](file:///Users/mayank/chatbot-retrieval/backend/ingestion/parent_chunker.py), [backend/retrieval/parent_retriever.py](file:///Users/mayank/chatbot-retrieval/backend/retrieval/parent_retriever.py) | **Completed** | Splits documents into parent-child hierarchies. Retrieval matches the child chunks but returns the parent context to the LLM. |
| **Cross-Encoder Reranker** | [backend/retrieval/reranker.py](file:///Users/mayank/chatbot-retrieval/backend/retrieval/reranker.py) | **Completed** | Integrates BAAI/bge-reranker-base to re-score candidate chunks for increased context accuracy. |
| **Orchestrator** | [backend/pipeline/conversational_chain.py](file:///Users/mayank/chatbot-retrieval/backend/pipeline/conversational_chain.py) | **Completed** | Stateful multi-turn conversation memory, automatically condensing queries. Auto-detects filename targets in queries using normalized name checks and overrides retrieval filters and thresholds. |
| **FastAPI Backend** | [backend/api/main.py](file:///Users/mayank/chatbot-retrieval/backend/api/main.py), [backend/Dockerfile](file:///Users/mayank/chatbot-retrieval/backend/Dockerfile) | **Completed** | REST endpoints for chat, delete, document ingestion, and health checks. Built as a containerized Python service listening on port 8000. |
| **React Frontend UI** | [frontend/Dockerfile](file:///Users/mayank/chatbot-retrieval/frontend/Dockerfile), [frontend/src/App.jsx](file:///Users/mayank/chatbot-retrieval/frontend/src/App.jsx) | **Completed** | Premium React SPA built with Vite and served on port 8501. Incorporates interactive 3D Three.js backgrounds, structured layout (Home, About, Dashboard), and complete telemetry/citations rendering. |
| **Embedding Cache** | [backend/ingestion/embedding_cache.py](file:///Users/mayank/chatbot-retrieval/backend/ingestion/embedding_cache.py) | **Completed** | Disk-based persistent embedding cache using diskcache to avoid redundant embedding generation and speed up ingestion. |
| **Document Registry** | [backend/ingestion/document_registry.py](file:///Users/mayank/chatbot-retrieval/backend/ingestion/document_registry.py) | **Completed** | Persistent JSON-based registry mapping indexed documents to rich metadata (size, file type, upload time, chunk count). |
| **Ablation Studies** | [backend/scripts/ablation_study.py](file:///Users/mayank/chatbot-retrieval/backend/scripts/ablation_study.py) | **Completed** | Automated parameter sweep framework evaluating retrieval recall and chunking optimization via Ragas. |
| **RAGAS Evaluation** | [backend/evaluation/ragas_eval.py](file:///Users/mayank/chatbot-retrieval/backend/evaluation/ragas_eval.py) | **Completed** | Uses llama3.2:3b for pipeline generation and mistral:7b as LLM judge with 180s timeout, score validation, and dataset size guard. |

---

## 4. Verification & Testing

### A. Container Deployments
Both documind-api and documind-ui build and maintain healthy statuses inside their respective workspaces when run under docker compose:
```bash
$ docker compose ps
NAME           IMAGE                            STATUS                   PORTS
documind-api   chatbot-retrieval-documind-api   Up 2 minutes (healthy)   0.0.0.0:8000->8000/tcp
documind-ui    chatbot-retrieval-documind-ui    Up 2 minutes             0.0.0.0:8501->8501/tcp
```

### B. Unit & Integration Testing
All unit tests pass successfully under the updated paths:
```bash
backend/tests/test_retrieval.py::test_embedding_dimension PASSED                 [ 14%]
backend/tests/test_retrieval.py::test_embedding_normalized PASSED                [ 28%]
backend/tests/test_retrieval.py::test_vector_store_add_and_search PASSED         [ 42%]
backend/tests/test_retrieval.py::test_context_builder PASSED                     [ 57%]
backend/tests/test_retrieval.py::test_context_builder_empty PASSED               [ 71%]
backend/tests/test_retrieval.py::test_reranker PASSED                            [ 85%]
backend/tests/test_retrieval.py::test_conversational_chain_condense PASSED       [100%]
```

### C. Automated RAGAS Evaluation
By upgrading the LLM judge model to mistral:7b and setting the Ollama timeout to 180 seconds, evaluation queries execute reliably without timeout errors, yielding precise scores across all Ragas metrics (Faithfulness, Answer Relevancy, Context Precision, and Context Recall).

---

## 5. Roadmap & Future Improvements
1. Ablation Studies:
   * Utilize the configuration settings framework to execute evaluations across varying chunk sizes and reranker top-K values to optimize retrieval recall.
2. Dynamic Context Windows:
   * Programmatically adjust retriever limits based on length checks of retrieved contexts to prevent context window overflow on local LLMs.
3. Advanced Session Memory:
   * Extend conversational chain state to support database-backed message stores and user session management.
