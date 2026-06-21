# Makefile — DocuMind Phase 12

.PHONY: serve ui ingest test lint clean eval warmup status

# ── Core runners ─────────────────────────────────────────────────────
serve:
	PYTHONPATH=backend uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

ui:
	cd frontend && npm run dev

# ── Document management ───────────────────────────────────────────────
ingest:
	PYTHONPATH=backend python backend/scripts/ingest_docs.py --source-dir backend/data/raw/

ingest-file:
	@test -n "$(FILE)" || (echo "Usage: make ingest-file FILE=backend/data/raw/doc.pdf" && exit 1)
	PYTHONPATH=backend python backend/scripts/ingest_docs.py --file $(FILE)

# ── Evaluation ───────────────────────────────────────────────────────
eval:
	PYTHONPATH=backend python backend/evaluation/ragas_eval.py

generate-eval:
	PYTHONPATH=backend python backend/scripts/generate_eval_dataset.py

benchmark:
	PYTHONPATH=backend python backend/scripts/benchmark_retrieval.py

# ── Development ───────────────────────────────────────────────────────
test:
	PYTHONPATH=backend pytest backend/tests/ -v --tb=short

lint:
	black backend/ && isort backend/ && flake8 backend/ --max-line-length=120 --exclude=.git,__pycache__,backend/data,backend/models

# ── Utilities ─────────────────────────────────────────────────────────
status:
	@echo "=== DocuMind Status ==="
	@echo "Ollama:"
	@curl -s http://localhost:11434/api/tags | python -m json.tool 2>/dev/null || echo "  Ollama not running. Start with: ollama serve"
	@echo "\nVector Store:"
	@PYTHONPATH=backend python -c "from retrieval.vector_store import VectorStore; s = VectorStore(); print(f'  Chunks stored: {s.count}'); print(f'  Sources: {s.list_sources()}')"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete 2>/dev/null; true
	@echo "Cleaned cache files."

clean-db:
	@echo "WARNING: This will delete ALL indexed documents from ChromaDB."
	@read -p "Are you sure? (y/N): " confirm && [ "$${confirm}" = "y" ] || exit 1
	rm -rf backend/data/chroma_db/*
	@echo "Vector store cleared."


# ── Ablation studies ──────────────────────────────────────────────────
ablation-chunks:
	PYTHONPATH=backend python backend/scripts/ablation_study.py \
		--param child_chunk_size --values 64 128 256

ablation-topk:
	PYTHONPATH=backend python backend/scripts/ablation_study.py \
		--param top_k --values 3 5 8

ablation-rerank:
	PYTHONPATH=backend python backend/scripts/ablation_study.py \
		--param reranker_candidates --values 10 20 30

ablation-fast:
	PYTHONPATH=backend python backend/scripts/ablation_study.py \
		--param child_chunk_size --values 64 128 256 --fast

ablation-summary:
	@cat backend/evaluation/ablation_summary.md 2>/dev/null || echo "No ablation results yet."

# ── Cache management ──────────────────────────────────────────────────
cache-stats:
	PYTHONPATH=backend python -c " \
from ingestion.embedder import EmbeddingService; \
e = EmbeddingService(); \
import json; print(json.dumps(e.cache_stats(), indent=2))"

cache-clear:
	@echo "WARNING: Clears all cached embedding vectors."
	@read -p "Confirm (y/N): " c && [ "$${c}" = "y" ] || exit 1
	PYTHONPATH=backend python -c "from ingestion.embedding_cache import EmbeddingCache; n=EmbeddingCache().clear(); print(f'Cleared {n} entries.')"

# ── Document manager ──────────────────────────────────────────────────
docs-list:
	@curl -s http://localhost:8000/api/v1/documents | python -m json.tool

docs-sync:
	PYTHONPATH=backend python -c " \
from ingestion.document_registry import DocumentRegistry; \
from retrieval.vector_store import VectorStore; \
reg = DocumentRegistry(); store = VectorStore(); \
n = reg.sync_with_store(store.list_sources()); \
print(f'Synced. Removed {n} stale entries.')"
