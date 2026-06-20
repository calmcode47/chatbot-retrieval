# Makefile — DocuMind Phase 12

.PHONY: serve ui ingest test lint clean eval warmup status

# ── Core runners ─────────────────────────────────────────────────────
serve:
	PYTHONPATH=. uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

ui:
	PYTHONPATH=. streamlit run ui/app.py --server.port 8501

# ── Document management ───────────────────────────────────────────────
ingest:
	PYTHONPATH=. python scripts/ingest_docs.py --source-dir data/raw/

ingest-file:
	@test -n "$(FILE)" || (echo "Usage: make ingest-file FILE=data/raw/doc.pdf" && exit 1)
	PYTHONPATH=. python scripts/ingest_docs.py --file $(FILE)

# ── Evaluation ───────────────────────────────────────────────────────
eval:
	PYTHONPATH=. python evaluation/ragas_eval.py

generate-eval:
	PYTHONPATH=. python scripts/generate_eval_dataset.py

benchmark:
	PYTHONPATH=. python scripts/benchmark_retrieval.py

# ── Development ───────────────────────────────────────────────────────
test:
	PYTHONPATH=. pytest tests/ -v --tb=short

lint:
	black . && isort . && flake8 . --max-line-length=120 --exclude=.git,__pycache__

# ── Utilities ─────────────────────────────────────────────────────────
status:
	@echo "=== DocuMind Status ==="
	@echo "Ollama:"
	@curl -s http://localhost:11434/api/tags | python -m json.tool 2>/dev/null || echo "  Ollama not running. Start with: ollama serve"
	@echo "\nVector Store:"
	@PYTHONPATH=. python -c "from retrieval.vector_store import VectorStore; s = VectorStore(); print(f'  Chunks stored: {s.count}'); print(f'  Sources: {s.list_sources()}')"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete 2>/dev/null; true
	@echo "Cleaned cache files."

clean-db:
	@echo "WARNING: This will delete ALL indexed documents from ChromaDB."
	@read -p "Are you sure? (y/N): " confirm && [ "$${confirm}" = "y" ] || exit 1
	rm -rf data/chroma_db/*
	@echo "Vector store cleared."


# ── Ablation studies ──────────────────────────────────────────────────
ablation-chunks:
	$(PYTHONPATH) python scripts/ablation_study.py \
		--param child_chunk_size --values 64 128 256

ablation-topk:
	$(PYTHONPATH) python scripts/ablation_study.py \
		--param top_k --values 3 5 8

ablation-rerank:
	$(PYTHONPATH) python scripts/ablation_study.py \
		--param reranker_candidates --values 10 20 30

ablation-fast:
	$(PYTHONPATH) python scripts/ablation_study.py \
		--param child_chunk_size --values 64 128 256 --fast

ablation-summary:
	@cat evaluation/ablation_summary.md 2>/dev/null || echo "No ablation results yet."

# ── Cache management ──────────────────────────────────────────────────
cache-stats:
	$(PYTHONPATH) python -c "
from ingestion.embedder import EmbeddingService
e = EmbeddingService()
import json; print(json.dumps(e.cache_stats(), indent=2))
"

cache-clear:
	@echo "WARNING: Clears all cached embedding vectors."
	@read -p "Confirm (y/N): " c && [ "$${c}" = "y" ] || exit 1
	$(PYTHONPATH) python -c "from ingestion.embedding_cache import EmbeddingCache; n=EmbeddingCache().clear(); print(f'Cleared {n} entries.')"

# ── Document manager ──────────────────────────────────────────────────
docs-list:
	@curl -s http://localhost:8000/api/v1/documents | python -m json.tool

docs-sync:
	$(PYTHONPATH) python -c "
from ingestion.document_registry import DocumentRegistry
from retrieval.vector_store import VectorStore
reg = DocumentRegistry(); store = VectorStore()
n = reg.sync_with_store(store.list_sources())
print(f'Synced. Removed {n} stale entries.')
"
