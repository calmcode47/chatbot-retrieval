# evaluation/ragas_eval.py
"""
RAGAS evaluation runner for DocuMind.

Measures pipeline quality across four metrics using local Ollama — no API keys.

Metrics:
  Faithfulness      — Is the answer grounded in retrieved context? (anti-hallucination)
  Answer Relevancy  — Does the answer address the question asked?
  Context Precision — Were retrieved chunks relevant? (no noise)
  Context Recall    — Were the right chunks retrieved? (completeness)

Run with: make eval
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
from loguru import logger


# ── Configuration ────────────────────────────────────────────────────
EVAL_DATASET_PATH  = "evaluation/eval_dataset.json"
RESULTS_PATH       = "evaluation/ragas_results.json"
OLLAMA_MODEL       = "llama3.2:3b"
OLLAMA_BASE_URL    = "http://localhost:11434"
TOP_K              = 5
RERANKER_CANDIDATES = 20
SCORE_THRESHOLD    = 0.0    # Disable threshold during eval — we want all chunks scored


def load_eval_dataset(path: str) -> list:
    """Load and validate the evaluation dataset."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found at '{path}'.\n"
            "Run: python scripts/generate_eval_dataset.py"
        )
    with open(p) as f:
        data = json.load(f)

    if not data:
        raise ValueError("Evaluation dataset is empty.")
    if len(data) < 5:
        logger.warning(f"Only {len(data)} questions. Aim for 10+ for reliable scores.")

    logger.info(f"Loaded {len(data)} evaluation questions.")
    return data


def build_ragas_dataset(eval_data: list) -> "Dataset":
    """
    Run each question through the live pipeline and collect:
    - The generated answer
    - The retrieved context chunks
    This builds the dataset RAGAS needs to evaluate.
    """
    from datasets import Dataset
    from ingestion.embedder import EmbeddingService
    from retrieval.vector_store import VectorStore
    from retrieval.reranker import CrossEncoderReranker
    from retrieval.context_builder import ContextBuilder
    from generation.llm import get_ollama_llm
    from generation.prompt_templates import get_rag_prompt

    embedder = EmbeddingService()
    store    = VectorStore()
    reranker = CrossEncoderReranker()
    builder  = ContextBuilder()
    llm      = get_ollama_llm(streaming=False)
    prompt   = get_rag_prompt()

    if store.count == 0:
        raise RuntimeError("Vector store is empty. Run 'make ingest' before evaluating.")

    questions, ground_truths, answers, contexts = [], [], [], []

    logger.info(f"Running {len(eval_data)} questions through the live pipeline...")

    for i, item in enumerate(eval_data):
        question     = item["question"]
        ground_truth = item["ground_truth"]

        logger.info(f"  [{i+1}/{len(eval_data)}] '{question[:70]}'")

        # Retrieval
        q_vec   = embedder.embed(question)
        results = store.search(q_vec, top_k=RERANKER_CANDIDATES)

        if reranker and results:
            results = reranker.rerank(question, results, top_k=TOP_K)

        # Context
        context_str, _ = builder.build(results, score_threshold=SCORE_THRESHOLD)
        context_chunks  = [r["document"] for r in results]

        # Generation
        messages = prompt.format_messages(context=context_str, question=question)
        response = llm.invoke(messages)
        answer   = response.content.strip()

        questions.append(question)
        ground_truths.append(ground_truth)
        answers.append(answer)
        contexts.append(context_chunks)

    return Dataset.from_dict({
        "question":    questions,
        "answer":      answers,
        "contexts":    contexts,
        "ground_truth": ground_truths,
    })


def run_ragas(dataset: "Dataset") -> dict:
    """Configure RAGAS to use local Ollama and run evaluation."""

    # Some RAGAS versions check for OpenAI key even when overriding the LLM.
    # Setting a placeholder prevents internal KeyError without making any API calls.
    os.environ.setdefault("OPENAI_API_KEY", "placeholder-not-used")

    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from langchain_ollama import ChatOllama
    from langchain_huggingface import HuggingFaceEmbeddings
    from ragas.run_config import RunConfig

    # Point RAGAS at local Ollama for both its LLM judge and embedding comparisons
    local_llm = LangchainLLMWrapper(
        ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0,          # Deterministic for evaluation
        )
    )
    local_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(
            model_name="BAAI/bge-base-en-v1.5"
        )
    )

    logger.info("Running RAGAS evaluation (expect 3–8 minutes depending on dataset size)...")
    logger.info("RAGAS uses your local Ollama model as the judge — no external APIs called.")

    # Configure run settings with a concurrency limit of 2 workers and 30s timeout
    config = RunConfig(max_workers=2, timeout=30.0)

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=local_llm,
        embeddings=local_embeddings,
        raise_exceptions=False,    # Log failures instead of crashing
        run_config=config,
    )

    import math
    def get_average_score(scores_list):
        if not isinstance(scores_list, list):
            try:
                val = float(scores_list)
                return 0.0 if math.isnan(val) else val
            except Exception:
                return 0.0
        valid_scores = [s for s in scores_list if s is not None and isinstance(s, (int, float)) and not math.isnan(s)]
        if not valid_scores:
            return 0.0
        return sum(valid_scores) / len(valid_scores)

    return {
        "faithfulness":      get_average_score(result["faithfulness"]),
        "answer_relevancy":  get_average_score(result["answer_relevancy"]),
        "context_precision": get_average_score(result["context_precision"]),
        "context_recall":    get_average_score(result["context_recall"]),
    }



def print_report(scores: dict, num_questions: int, elapsed: float):
    """Pretty-print results with interpretation."""

    targets = {
        "faithfulness":      0.80,
        "answer_relevancy":  0.80,
        "context_precision": 0.70,
        "context_recall":    0.70,
    }

    descriptions = {
        "faithfulness":      "Is the answer grounded in context? (anti-hallucination)",
        "answer_relevancy":  "Does the answer address the question?",
        "context_precision": "Were retrieved chunks relevant? (no noise)",
        "context_recall":    "Were the right chunks retrieved? (completeness)",
    }

    print("\n" + "=" * 70)
    print("  RAGAS EVALUATION RESULTS")
    print("=" * 70)
    print(f"  Questions evaluated : {num_questions}")
    print(f"  Evaluation time     : {elapsed:.0f}s")
    print(f"  LLM judge           : {OLLAMA_MODEL} (local)")
    print()

    for metric, score in scores.items():
        target = targets[metric]
        desc   = descriptions[metric]
        if score >= target:
            status = f"✓  GOOD    (target ≥ {target:.2f})"
        elif score >= target - 0.10:
            status = f"⚠  CLOSE   (target ≥ {target:.2f})"
        else:
            status = f"✗  IMPROVE (target ≥ {target:.2f})"
        print(f"  {metric:<25}  {score:.4f}  {status}")
        print(f"  {'':25}  {desc}")
        print()

    print("=" * 70)

    # Targeted improvement guide
    print("\n  Improvement actions:")
    if scores["context_recall"] < 0.70:
        print("  → context_recall LOW  : Increase top_k (try 8). Reduce chunk_size to 256.")
    if scores["context_precision"] < 0.70:
        print("  → context_precision   : Raise score_threshold (try 0.45). Enable reranker.")
    if scores["faithfulness"] < 0.80:
        print("  → faithfulness LOW    : Strengthen system prompt. Set temperature=0.0.")
        print("                          Try mistral:7b for a better instruction-following model.")
    if scores["answer_relevancy"] < 0.80:
        print("  → answer_relevancy    : LLM may be drifting. Check RAG system prompt.")
    if all(v >= targets[k] for k, v in scores.items()):
        print("  → All metrics at target. Your pipeline is production quality.")

    print()


def main():
    total_start = time.time()

    # Load eval dataset
    eval_data = load_eval_dataset(EVAL_DATASET_PATH)

    # Build dataset by running live pipeline
    ragas_dataset = build_ragas_dataset(eval_data)

    # Run RAGAS with local Ollama
    ragas_start = time.time()
    scores = run_ragas(ragas_dataset)
    ragas_elapsed = time.time() - ragas_start

    # Print formatted report
    print_report(scores, num_questions=len(eval_data), elapsed=ragas_elapsed)

    # Persist results
    output = {
        "timestamp":              datetime.now().isoformat(),
        "num_questions":          len(eval_data),
        "llm_judge":              OLLAMA_MODEL,
        "metrics":                scores,
        "ragas_time_seconds":     round(ragas_elapsed, 1),
        "total_time_seconds":     round(time.time() - total_start, 1),
    }

    Path(RESULTS_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(output, f, indent=2)

    logger.success(f"Results saved → {RESULTS_PATH}")


if __name__ == "__main__":
    main()
