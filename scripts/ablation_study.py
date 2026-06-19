# scripts/ablation_study.py
"""
Single-parameter ablation study for DocuMind.

Iterates over values of one config parameter, re-ingests documents,
runs RAGAS evaluation, and records scores.

Usage:
  # Sweep child_chunk_size
  python scripts/ablation_study.py --param child_chunk_size --values 64 128 256

  # Sweep top_k (use optimal child_chunk_size from previous sweep first)
  python scripts/ablation_study.py --param top_k --values 3 5 8

  # Fast mode: 5 questions per run (less accurate but ~3x faster)
  python scripts/ablation_study.py --param child_chunk_size --values 64 128 256 --fast

  # Results are saved to: evaluation/ablation_results.json
  # Summary table is printed and saved to: evaluation/ablation_summary.md
"""

import argparse
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

from loguru import logger


SUPPORTED_PARAMS = {
    "child_chunk_size":    ("chunking",   int),
    "parent_chunk_size":   ("chunking",   int),
    "top_k":               ("retrieval",  int),
    "reranker_candidates": ("retrieval",  int),
    "score_threshold":     ("retrieval",  float),
}

RESULTS_PATH = Path("evaluation/ablation_results.json")
SUMMARY_PATH = Path("evaluation/ablation_summary.md")
DATA_DIR     = Path("data/raw")
CHROMA_DIR   = Path("data/chroma_db")


# ── Config override (in-memory, no YAML rewrite) ─────────────────────

def override_config(param: str, value) -> None:
    """
    Temporarily override a config value in-memory for this run.
    Does NOT rewrite config.yaml — only affects the current process.
    Uses the get_config.cache_clear() + environment variable approach.
    """
    from configs.settings import get_config
    get_config.cache_clear()

    section, _ = SUPPORTED_PARAMS[param]
    env_key     = f"ABLATION_{param.upper()}"
    os.environ[env_key] = str(value)

    # The settings loader must read this env var.
    # We patch it directly on the loaded config for simplicity:
    cfg = get_config()
    sub = getattr(cfg, section)
    setattr(sub, param, value)
    logger.info(f"Config override: {section}.{param} = {value}")


# ── Pipeline operations ───────────────────────────────────────────────

def clear_vector_store() -> None:
    """Wipe ChromaDB for a clean re-ingest."""
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("ChromaDB cleared.")
    # Also reset the in-memory store in case it's imported
    from configs.settings import get_config
    get_config.cache_clear()


def ingest_all_documents(use_hierarchical: bool = True) -> int:
    """Ingest all documents from data/raw/ using current config."""
    from ingestion.embedder import EmbeddingService
    from ingestion.loaders import load_file
    from ingestion.parent_chunker import ParentDocumentChunker
    from ingestion.chunker import DocumentChunker
    from retrieval.vector_store import VectorStore
    from configs.settings import get_config
    import uuid

    cfg      = get_config()
    embedder = EmbeddingService(
        model_name=cfg.embedding.model_name,
        device=cfg.embedding.device,
        use_cache=True,
    )
    store    = VectorStore(persist_directory=str(CHROMA_DIR))

    files = list(DATA_DIR.glob("**/*.pdf")) + \
            list(DATA_DIR.glob("**/*.txt")) + \
            list(DATA_DIR.glob("**/*.md"))

    if not files:
        raise RuntimeError(f"No documents found in '{DATA_DIR}'. Add documents before running ablation.")

    total_chunks = 0

    for file_path in files:
        documents = load_file(str(file_path))

        if use_hierarchical:
            chunker = ParentDocumentChunker()
            hier_chunks = chunker.split(documents)
            texts = [c.child_text for c in hier_chunks]
            metadatas = [
                {
                    "source_file":  file_path.name,
                    "parent_id":    c.parent_id,
                    "parent_text":  c.parent_text,
                    "child_index":  c.child_index,
                }
                for c in hier_chunks
            ]
        else:
            chunker = DocumentChunker()
            chunks = chunker.split(documents)
            texts = [c.page_content for c in chunks]
            metadatas = [{"source_file": file_path.name, **c.metadata} for c in chunks]

        embeddings = embedder.embed_batch(texts)
        ids = [f"{file_path.name}_{i}_{uuid.uuid4().hex[:6]}" for i in range(len(texts))]
        store.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        total_chunks += len(texts)
        logger.info(f"  Ingested '{file_path.name}': {len(texts)} chunks")

    logger.success(f"Ingestion complete: {total_chunks} total chunks")
    return total_chunks


def run_ragas_evaluation(fast_mode: bool = False) -> dict:
    """
    Run RAGAS evaluation using the current pipeline configuration.
    fast_mode=True uses only the first 5 eval questions (quicker, less accurate).
    """
    import importlib
    import evaluation.ragas_eval as ragas_module
    importlib.reload(ragas_module)   # Reload to pick up any config changes

    eval_path = Path(ragas_module.EVAL_DATASET_PATH)
    if not eval_path.exists():
        raise FileNotFoundError(
            f"Eval dataset not found at '{eval_path}'. "
            "Run: python scripts/generate_eval_dataset.py"
        )

    with open(eval_path) as f:
        eval_data = json.load(f)

    if fast_mode:
        eval_data = eval_data[:5]
        logger.info("Fast mode: using first 5 eval questions only")

    if len(eval_data) < 3:
        raise ValueError(
            f"Only {len(eval_data)} eval questions after selection. "
            "Need at least 3. Run: python scripts/generate_eval_dataset.py"
        )

    ragas_dataset = ragas_module.build_ragas_dataset(eval_data)
    scores        = ragas_module.run_ragas_with_judge(ragas_dataset)
    return scores


# ── Results management ────────────────────────────────────────────────

def load_results() -> dict:
    if RESULTS_PATH.exists():
        with open(RESULTS_PATH) as f:
            return json.load(f)
    return {"runs": []}


def save_results(data: dict) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def generate_summary(results: dict) -> str:
    """Generate a markdown comparison table from ablation results."""
    runs = results.get("runs", [])
    if not runs:
        return "No ablation results yet."

    # Group by parameter
    by_param: dict = {}
    for run in runs:
        param = run["param"]
        by_param.setdefault(param, []).append(run)

    lines = ["# DocuMind — Ablation Study Results\n"]
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    for param, param_runs in by_param.items():
        lines.append(f"\n## Parameter: `{param}`\n")
        lines.append("| Value | Faithfulness | Answer Rel. | Ctx Precision | Ctx Recall | Avg |")
        lines.append("|---|---|---|---|---|---|")

        best_avg   = -1
        best_value = None

        for run in sorted(param_runs, key=lambda x: x["value"]):
            m     = run["metrics"]
            faith = m.get("faithfulness", 0)
            ar    = m.get("answer_relevancy", 0)
            cp    = m.get("context_precision", 0)
            cr    = m.get("context_recall", 0)
            avg   = (faith + ar + cp + cr) / 4

            if avg > best_avg:
                best_avg   = avg
                best_value = run["value"]

            lines.append(
                f"| {run['value']} | {faith:.4f} | {ar:.4f} | {cp:.4f} | {cr:.4f} | **{avg:.4f}** |"
            )

        lines.append(f"\n**Best value: `{best_value}` (avg score: {best_avg:.4f})**\n")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run single-parameter ablation study for DocuMind"
    )
    parser.add_argument(
        "--param",
        required=True,
        choices=list(SUPPORTED_PARAMS.keys()),
        help="Config parameter to sweep",
    )
    parser.add_argument(
        "--values",
        nargs="+",
        required=True,
        help="Values to test (e.g., --values 64 128 256)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode: use only 5 eval questions per run (less accurate, ~3x faster)",
    )
    parser.add_argument(
        "--no-hierarchical",
        action="store_true",
        help="Use flat chunking instead of hierarchical",
    )
    args = parser.parse_args()

    _, type_fn = SUPPORTED_PARAMS[args.param]
    values     = [type_fn(v) for v in args.values]
    hierarchical = not args.no_hierarchical

    logger.info(f"Ablation study: {args.param} ∈ {values}")
    logger.info(f"Fast mode: {args.fast} | Hierarchical: {hierarchical}")

    if args.fast:
        logger.warning("Fast mode enabled: scores less reliable (5 questions only). Use for direction, not final results.")

    results = load_results()

    for value in values:
        run_id = f"{args.param}={value}_{'fast' if args.fast else 'full'}_{datetime.now().strftime('%H%M%S')}"
        logger.info(f"\n{'='*60}")
        logger.info(f"Run: {run_id}")
        logger.info(f"{'='*60}")

        run_start = time.time()

        try:
            # 1. Override config
            override_config(args.param, value)

            # 2. Clear and re-ingest
            logger.info("Clearing vector store...")
            clear_vector_store()

            logger.info("Re-ingesting documents...")
            chunk_count = ingest_all_documents(use_hierarchical=hierarchical)

            # 3. Run RAGAS
            logger.info("Running RAGAS evaluation...")
            scores = run_ragas_evaluation(fast_mode=args.fast)

            elapsed = time.time() - run_start

            # 4. Record result
            run_record = {
                "run_id":       run_id,
                "param":        args.param,
                "value":        value,
                "fast_mode":    args.fast,
                "chunk_count":  chunk_count,
                "metrics":      scores,
                "elapsed_s":    round(elapsed, 1),
                "timestamp":    datetime.now().isoformat(),
            }

            results["runs"].append(run_record)
            save_results(results)

            logger.success(f"Run complete in {elapsed/60:.1f} min:")
            for metric, score in scores.items():
                logger.info(f"  {metric:<25} {score:.4f}")

        except Exception as e:
            logger.error(f"Run {run_id} failed: {e}")
            results["runs"].append({
                "run_id":    run_id,
                "param":     args.param,
                "value":     value,
                "error":     str(e),
                "timestamp": datetime.now().isoformat(),
            })
            save_results(results)
            continue

    # Generate and save summary table
    summary = generate_summary(results)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_PATH, "w") as f:
        f.write(summary)

    print("\n" + summary)
    logger.success(f"Summary saved → {SUMMARY_PATH}")
    logger.success(f"Full results  → {RESULTS_PATH}")


if __name__ == "__main__":
    main()
