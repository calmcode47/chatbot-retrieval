# evaluation/ragas_eval.py
"""
RAGAS evaluation for DocuMind RAG pipeline.

Measures:
  - Faithfulness:       Is the answer grounded in the retrieved context?
  - Answer Relevancy:   Does the answer address the question?
  - Context Precision:  Were retrieved chunks relevant (no noise)?
  - Context Recall:     Did retrieval find the right information?

Run with: make eval
"""

import json
import time
from pathlib import Path
from datetime import datetime

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from loguru import logger

from ingestion.embedder import EmbeddingService
from retrieval.vector_store import VectorStore
from retrieval.context_builder import ContextBuilder
from retrieval.reranker import CrossEncoderReranker
from generation.llm import get_ollama_llm


EVAL_DATASET_PATH = "evaluation/eval_dataset.json"
RESULTS_OUTPUT_PATH = "evaluation/ragas_results.json"


def build_ragas_dataset(
    embedder: EmbeddingService,
    store: VectorStore,
    reranker: CrossEncoderReranker,
    context_builder: ContextBuilder,
    eval_data: list,
    top_k: int = 5,
    reranker_candidates: int = 20,
) -> Dataset:
    """
    For each question in eval_data, retrieve contexts using the live pipeline
    and build a RAGAS-compatible dataset.
    """
    questions = []
    ground_truths = []
    answers = []
    contexts = []

    llm = get_ollama_llm(streaming=False)

    from generation.prompt_templates import get_rag_prompt
    rag_prompt = get_rag_prompt()

    logger.info(f"Building RAGAS dataset from {len(eval_data)} evaluation questions...")

    for i, item in enumerate(eval_data):
        question = item["question"]
        ground_truth = item["ground_truth"]
        logger.info(f"  [{i+1}/{len(eval_data)}] Processing: '{question[:60]}'")

        # Retrieve
        q_vec = embedder.embed(question)
        results = store.search(q_vec, top_k=reranker_candidates)

        # Rerank
        if reranker and results:
            results = reranker.rerank(question, results, top_k=top_k)

        # Build context
        context_str, sources = context_builder.build(results, score_threshold=0.0)  # threshold=0 for eval
        context_chunks = [r["document"] for r in results]

        # Generate answer
        messages = rag_prompt.format_messages(context=context_str, question=question)
        response = llm.invoke(messages)
        answer = response.content

        questions.append(question)
        ground_truths.append(ground_truth)
        answers.append(answer)
        contexts.append(context_chunks)

        logger.debug(f"    Answer: '{answer[:100]}...'")

    return Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })


def run_evaluation():
    """Main evaluation runner."""

    # Load eval dataset
    eval_path = Path(EVAL_DATASET_PATH)
    if not eval_path.exists():
        logger.error(f"Evaluation dataset not found at '{EVAL_DATASET_PATH}'.")
        logger.info("Create it manually or run: python scripts/generate_eval_dataset.py")
        return

    with open(eval_path) as f:
        eval_data = json.load(f)

    if len(eval_data) < 3:
        logger.warning(f"Only {len(eval_data)} questions in eval dataset. Add more for reliable scores (aim for 10+).")

    # Initialize pipeline components
    embedder = EmbeddingService()
    store = VectorStore()
    reranker = CrossEncoderReranker()
    context_builder = ContextBuilder()

    if store.count == 0:
        logger.error("Vector store is empty. Run 'make ingest' before evaluating.")
        return

    logger.info(f"Vector store has {store.count} chunks. Starting evaluation...")

    # Build RAGAS dataset using live pipeline
    ragas_dataset = build_ragas_dataset(
        embedder=embedder,
        store=store,
        reranker=reranker,
        context_builder=context_builder,
        eval_data=eval_data,
    )

    # Configure RAGAS to use local Ollama (no external APIs)
    from langchain_ollama import ChatOllama, OllamaEmbeddings

    local_llm = LangchainLLMWrapper(
        ChatOllama(model="llama3.2:3b", base_url="http://localhost:11434", temperature=0)
    )
    local_embeddings = LangchainEmbeddingsWrapper(
        OllamaEmbeddings(model="llama3.2:3b", base_url="http://localhost:11434")
    )

    # Run RAGAS evaluation
    logger.info("Running RAGAS evaluation (this may take several minutes)...")
    start = time.time()

    result = evaluate(
        dataset=ragas_dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=local_llm,
        embeddings=local_embeddings,
        raise_exceptions=False,
    )

    elapsed = time.time() - start

    # Print results
    print("\n" + "="*60)
    print("RAGAS EVALUATION RESULTS")
    print("="*60)
    print(f"  Faithfulness:       {result['faithfulness']:.4f}   (is answer grounded in context?)")
    print(f"  Answer Relevancy:   {result['answer_relevancy']:.4f}   (does answer address the question?)")
    print(f"  Context Precision:  {result['context_precision']:.4f}   (were retrieved chunks relevant?)")
    print(f"  Context Recall:     {result['context_recall']:.4f}   (were the right chunks retrieved?)")
    print(f"\n  Evaluation time:    {elapsed:.1f}s over {len(eval_data)} questions")
    print("="*60)

    # Grade interpretation
    scores = {
        "faithfulness": result["faithfulness"],
        "answer_relevancy": result["answer_relevancy"],
        "context_precision": result["context_precision"],
        "context_recall": result["context_recall"],
    }

    print("\nDiagnosis:")
    for metric, score in scores.items():
        if score >= 0.80:
            status = "✓ GOOD"
        elif score >= 0.65:
            status = "⚠ ACCEPTABLE — room for improvement"
        else:
            status = "✗ NEEDS WORK — see improvement guide below"
        print(f"  {metric:<25} {score:.3f}  {status}")

    # Save results to disk
    output = {
        "timestamp": datetime.now().isoformat(),
        "num_questions": len(eval_data),
        "metrics": scores,
        "evaluation_time_seconds": round(elapsed, 2),
    }

    with open(RESULTS_OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    logger.success(f"Results saved to '{RESULTS_OUTPUT_PATH}'")

    # Improvement suggestions
    print("\nImprovement Guide:")
    if scores["context_recall"] < 0.70:
        print("  → Low context_recall: Increase top_k (try 8 or 10). Reduce chunk_size (try 256).")
    if scores["context_precision"] < 0.70:
        print("  → Low context_precision: Raise score_threshold (try 0.5). The reranker should help here.")
    if scores["faithfulness"] < 0.75:
        print("  → Low faithfulness: Strengthen system prompt. Lower temperature to 0.0. Try mistral:7b.")
    if scores["answer_relevancy"] < 0.75:
        print("  → Low answer_relevancy: Check prompt template. LLM may be drifting off-topic.")


if __name__ == "__main__":
    run_evaluation()
