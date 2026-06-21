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

## Deployment
* Fully containerized using Docker and Docker Compose.
* Local Makefile recipes for easy development.
