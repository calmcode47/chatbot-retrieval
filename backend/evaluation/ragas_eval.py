# evaluation/ragas_eval.py
"""
RAGAS evaluation runner — Phase 14 fix.

Two-model strategy:
  RAG pipeline  → llama3.2:3b  (fast, good at Q&A)
  RAGAS judge   → mistral:7b   (reliable structured JSON output for evaluation)

Key changes from Phase 13:
  - RunConfig with 180s timeout per LLM call (was 30s)
  - mistral:7b as judge to avoid malformed JSON
  - Score validation warns when metrics are suspiciously zero
  - Dataset size guard (minimum 10 questions)

Run with: make eval
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

from loguru import logger

# ── Configuration ────────────────────────────────────────────────────
RAG_MODEL = "llama3.2:3b"  # Model used by your RAG pipeline
JUDGE_MODEL = "mistral:7b"  # Model used as RAGAS judge
OLLAMA_BASE_URL = "http://localhost:11434"
EVAL_DATASET_PATH = "evaluation/eval_dataset.json"
RESULTS_PATH = "evaluation/ragas_results.json"

TOP_K = 5
RERANKER_CANDIDATES = 20
MIN_QUESTIONS = 10  # Refuse to run below this count

# Targets for each metric
TARGETS = {
    "faithfulness": 0.80,
    "answer_relevancy": 0.80,
    "context_precision": 0.70,
    "context_recall": 0.70,
}

DESCRIPTIONS = {
    "faithfulness": "Is the answer grounded in context? (anti-hallucination)",
    "answer_relevancy": "Does the answer address the question?",
    "context_precision": "Were retrieved chunks relevant? (no noise)",
    "context_recall": "Were the right chunks retrieved? (completeness)",
}


# ── Step 1: Load evaluation dataset ─────────────────────────────────
def load_eval_dataset() -> list:
    p = Path(EVAL_DATASET_PATH)
    if not p.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found at '{EVAL_DATASET_PATH}'.\n"
            "Run: python scripts/generate_eval_dataset.py"
        )
    with open(p) as f:
        data = json.load(f)

    if len(data) < MIN_QUESTIONS:
        raise ValueError(
            f"Only {len(data)} questions in eval dataset. "
            f"Need at least {MIN_QUESTIONS} for reliable scores.\n"
            "Add more documents and re-run: python scripts/generate_eval_dataset.py"
        )

    logger.info(f"Loaded {len(data)} evaluation questions.")
    return data


# ── Step 2: Build RAGAS dataset by running the live pipeline ─────────
def build_ragas_dataset(eval_data: list) -> "Dataset":
    """Run each question through the RAG pipeline and collect answers + contexts."""
    from datasets import Dataset
    from generation.prompt_templates import get_rag_prompt
    from ingestion.embedder import EmbeddingService
    from langchain_ollama import ChatOllama
    from retrieval.context_builder import ContextBuilder
    from retrieval.reranker import CrossEncoderReranker
    from retrieval.vector_store import VectorStore

    embedder = EmbeddingService()
    store = VectorStore()
    reranker = CrossEncoderReranker()
    builder = ContextBuilder()
    prompt = get_rag_prompt()

    # Use the RAG model (small, fast) — this is not the judge
    rag_llm = ChatOllama(
        model=RAG_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,
    )

    if store.count == 0:
        raise RuntimeError(
            "Vector store is empty. Run 'make ingest' before evaluating."
        )

    questions, ground_truths, answers, contexts = [], [], [], []

    logger.info(
        f"Running {len(eval_data)} questions through RAG pipeline (model: {RAG_MODEL})..."
    )

    for i, item in enumerate(eval_data):
        question = item["question"]
        ground_truth = item["ground_truth"]

        logger.info(f"  [{i+1}/{len(eval_data)}] {question[:70]}")

        try:
            q_vec = embedder.embed(question)
            results = store.search(q_vec, top_k=RERANKER_CANDIDATES)

            if reranker and results:
                results = reranker.rerank(question, results, top_k=TOP_K)

            # score_threshold=0 during eval — we want all chunks judged by RAGAS
            context_str, _ = builder.build(results, score_threshold=0.0)
            context_chunks = [r["document"] for r in results]

            messages = prompt.format_messages(context=context_str, question=question)
            response = rag_llm.invoke(messages)
            answer = response.content.strip()

            questions.append(question)
            ground_truths.append(ground_truth)
            answers.append(answer)
            contexts.append(context_chunks)

        except Exception as e:
            logger.warning(f"    Pipeline error on question {i+1}: {e}. Skipping.")
            continue

    if not questions:
        raise RuntimeError(
            "No questions processed successfully. Check pipeline and Ollama."
        )

    logger.success(f"Pipeline complete. {len(questions)} answers collected.")

    return Dataset.from_dict(
        {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        }
    )


# ── Step 3: Run RAGAS with mistral:7b as judge ───────────────────────
def run_ragas_with_judge(dataset: "Dataset") -> dict:
    """
    Configure RAGAS to use mistral:7b as judge.

    Why mistral:7b instead of llama3.2:3b:
      - Reliably produces structured JSON output that RAGAS can parse
      - Stronger reasoning for NLI tasks (faithfulness, context precision)
      - Better instruction-following for question generation (answer relevancy)
      - 180s timeout gives it time to finish complex prompts
    """
    # Some RAGAS versions internally check for this key.
    # Setting a placeholder prevents KeyError without making any external calls.
    os.environ.setdefault("OPENAI_API_KEY", "placeholder-not-used")

    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_ollama import ChatOllama
    from ragas import evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (answer_relevancy, context_precision,
                               context_recall, faithfulness)
    from ragas.run_config import RunConfig

    # RAGAS judge: mistral:7b (strong reasoning, reliable JSON)
    judge_llm = LangchainLLMWrapper(
        ChatOllama(
            model=JUDGE_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0,  # Deterministic for evaluation
        )
    )

    # BGE embeddings for answer_relevancy similarity computation
    judge_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    )

    # Critical: 180s timeout and max_workers=1 (run sequentially to prevent local Ollama timeouts)
    run_config = RunConfig(
        timeout=180,  # Seconds per individual LLM call — was 30s
        max_retries=2,  # Retry on transient failure
        max_wait=60,  # Max seconds between retries
        max_workers=1,  # Run sequentially to avoid local CPU/GPU queue timeout
    )

    logger.info(f"Running RAGAS evaluation (judge: {JUDGE_MODEL})...")
    logger.info("Expected duration: 10–30 minutes depending on dataset size.")
    logger.info(
        "This is normal — mistral:7b evaluating each question is slow but accurate."
    )

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=judge_llm,
        embeddings=judge_embeddings,
        run_config=run_config,
        raise_exceptions=False,
    )

    import math

    def get_average_score(scores_list):
        if not isinstance(scores_list, list):
            try:
                val = float(scores_list)
                return 0.0 if math.isnan(val) else val
            except Exception:
                return 0.0
        valid_scores = [
            s
            for s in scores_list
            if s is not None and isinstance(s, (int, float)) and not math.isnan(s)
        ]
        if not valid_scores:
            return 0.0
        return sum(valid_scores) / len(valid_scores)

    return {
        "faithfulness": get_average_score(result["faithfulness"]),
        "answer_relevancy": get_average_score(result["answer_relevancy"]),
        "context_precision": get_average_score(result["context_precision"]),
        "context_recall": get_average_score(result["context_recall"]),
    }


# ── Step 4: Validate scores and print report ────────────────────────
def validate_scores(scores: dict) -> list[str]:
    """
    Detect suspiciously zero scores and explain likely causes.
    Returns a list of warning strings (empty = all good).
    """
    warnings = []

    if scores["faithfulness"] == 0.0:
        warnings.append(
            "faithfulness = 0.0 → Judge model may still be timing out. "
            "Check: ollama run mistral:7b 'Return JSON: {\"x\": 1}' "
            "If it produces valid JSON, increase RunConfig timeout further."
        )

    if scores["answer_relevancy"] == 0.0:
        warnings.append(
            "answer_relevancy = 0.0 → Reverse question generation failed. "
            "Verify: ollama pull mistral:7b completed without errors."
        )

    if scores["context_precision"] == 0.0:
        warnings.append(
            "context_precision = 0.0 → Context relevance judgment failed. "
            "Try: increase RunConfig timeout to 240s and re-run."
        )

    if all(v == 0.0 for k, v in scores.items() if k != "context_recall"):
        warnings.append(
            "CRITICAL: All LLM-based metrics are 0.0. "
            "Ollama may not be running, or mistral:7b is not pulled. "
            "Run: ollama pull mistral:7b && ollama serve"
        )

    return warnings


def print_report(scores: dict, num_questions: int, elapsed: float, judge_model: str):
    print("\n" + "=" * 68)
    print("  RAGAS EVALUATION RESULTS")
    print("=" * 68)
    print(f"  Questions     : {num_questions}")
    print(f"  LLM Judge     : {judge_model}")
    print(f"  RAG Model     : {RAG_MODEL}")
    print(f"  Eval time     : {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print()

    for metric, score in scores.items():
        target = TARGETS[metric]
        desc = DESCRIPTIONS[metric]
        if score >= target:
            tag = f"✓  GOOD    (≥ {target:.2f})"
        elif score > 0.0:
            tag = f"⚠  CLOSE   (target: {target:.2f})"
        else:
            tag = f"✗  FAILED  (0.0 — see warnings below)"
        print(f"  {metric:<25} {score:.4f}  {tag}")
        print(f"  {'':25}  {desc}")
        print()

    print("=" * 68)

    # Warnings
    warnings = validate_scores(scores)
    if warnings:
        print("\n  Warnings:")
        for w in warnings:
            print(f"  ⚠ {w}")
        print()

    # Improvement guide (only for non-zero scores)
    if any(v > 0 for v in scores.values()):
        print("  Improvement actions:")
        if 0 < scores["context_recall"] < 0.70:
            print(
                "  → context_recall LOW : Increase top_k to 8. Reduce child_chunk_size to 96."
            )
        if 0 < scores["context_precision"] < 0.70:
            print(
                "  → context_precision  : Raise score_threshold to 0.45. Reranker should help."
            )
        if 0 < scores["faithfulness"] < 0.80:
            print(
                "  → faithfulness LOW   : Strengthen system prompt. Set temperature=0.0."
            )
        if 0 < scores["answer_relevancy"] < 0.80:
            print(
                "  → answer_relevancy   : Check RAG prompt template for off-topic drift."
            )
        if all(v >= TARGETS[k] for k, v in scores.items()):
            print("  → All metrics at target. Pipeline is production quality.")
    print()


def main():
    total_start = time.time()

    # Load and validate dataset
    eval_data = load_eval_dataset()

    # Run RAG pipeline to collect answers
    ragas_dataset = build_ragas_dataset(eval_data)

    # Run RAGAS judge with mistral:7b
    judge_start = time.time()
    scores = run_ragas_with_judge(ragas_dataset)
    judge_elapsed = time.time() - judge_start

    # Print report
    print_report(
        scores,
        num_questions=len(eval_data),
        elapsed=judge_elapsed,
        judge_model=JUDGE_MODEL,
    )

    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "num_questions": len(eval_data),
        "rag_model": RAG_MODEL,
        "judge_model": JUDGE_MODEL,
        "metrics": scores,
        "judge_time_seconds": round(judge_elapsed, 1),
        "total_time_seconds": round(time.time() - total_start, 1),
    }

    Path(RESULTS_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(output, f, indent=2)

    logger.success(f"Results saved → {RESULTS_PATH}")

    # Exit code: non-zero if any metric is critically below target
    any_failed = any(scores[k] == 0.0 for k in ["faithfulness", "answer_relevancy"])
    if any_failed:
        logger.error(
            "Evaluation incomplete — some metrics are still 0.0. See warnings above."
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
