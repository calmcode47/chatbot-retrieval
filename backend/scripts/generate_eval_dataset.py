# scripts/generate_eval_dataset.py
"""
Synthetic evaluation dataset generator.

For each chunk in ChromaDB, uses Ollama to generate a grounded question
and expected answer. The result is saved as evaluation/eval_dataset.json.

Run with: python scripts/generate_eval_dataset.py
"""

import json
import time
from pathlib import Path

import httpx
from loguru import logger

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"
OUTPUT_PATH = "evaluation/eval_dataset.json"
MAX_QUESTIONS = 25  # Cap at 25 — enough for reliable RAGAS scores
MIN_CHUNK_LENGTH = 80  # Skip very short chunks that won't generate useful questions


GENERATION_PROMPT = """You are creating evaluation data for a document Q&A system.

Given the following passage from a document, generate ONE specific question that:
1. Can be answered ONLY using information in this passage
2. Requires reading the passage to answer (not general knowledge)
3. Has a clear, factual answer

Then provide the correct answer from the passage.

Passage:
{chunk}

Respond in this exact JSON format (no other text, no markdown):
{{"question": "your question here", "answer": "the answer from the passage"}}"""


def call_ollama(prompt: str, timeout: int = 60) -> str | None:
    """Make a synchronous call to the Ollama REST API."""
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 200},
                },
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
    except httpx.ConnectError:
        logger.error("Cannot reach Ollama. Run: ollama serve")
        return None
    except Exception as e:
        logger.warning(f"Ollama call failed: {e}")
        return None


def generate_dataset():
    from retrieval.vector_store import VectorStore

    store = VectorStore()

    if store.count < 20:
        logger.error(
            f"Vector store contains only {store.count} chunks. "
            "Must be at least 20 before generating evaluation data. "
            "Please run 'make ingest' first or add more documents."
        )
        return

    logger.info(f"Fetching chunks from ChromaDB ({store.count} total)...")

    # Fetch all stored chunks
    all_data = store.collection.get(include=["documents", "metadatas"])
    chunks = all_data["documents"]
    metadatas = all_data["metadatas"]

    # Filter out very short chunks
    eligible = [
        (text, meta)
        for text, meta in zip(chunks, metadatas)
        if len(text.strip()) >= MIN_CHUNK_LENGTH
    ]

    logger.info(f"Eligible chunks for question generation: {len(eligible)}")

    if len(eligible) < 5:
        logger.error(
            f"Only {len(eligible)} eligible chunks. "
            "Add more documents (target: 15+ chunks) before generating evaluation data."
        )
        return

    # Sample evenly across documents for coverage
    import random

    random.shuffle(eligible)
    selected = eligible[:MAX_QUESTIONS]

    dataset = []
    skipped = 0

    for i, (chunk_text, meta) in enumerate(selected):
        logger.info(
            f"  [{i+1}/{len(selected)}] Generating Q&A for chunk from '{meta.get('source_file', '?')}'"
        )

        prompt = GENERATION_PROMPT.format(
            chunk=chunk_text[:800]
        )  # Cap chunk for prompt budget
        raw_response = call_ollama(prompt)

        if not raw_response:
            skipped += 1
            continue

        # Parse JSON response — handle common LLM formatting artifacts
        try:
            # Strip markdown fences if present
            clean = raw_response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            parsed = json.loads(clean.strip())

            question = parsed.get("question", "").strip()
            answer = parsed.get("answer", "").strip()

            if not question or not answer or len(question) < 10:
                logger.debug(f"    Skipping — invalid response: {raw_response[:80]}")
                skipped += 1
                continue

            dataset.append(
                {
                    "question": question,
                    "ground_truth": answer,
                    "source_doc": meta.get("source_file", "unknown"),
                    "source_chunk": chunk_text[:300],  # For manual review
                }
            )

            logger.debug(f"    Q: {question[:80]}")

        except json.JSONDecodeError:
            logger.debug(f"    Skipping — JSON parse failed: {raw_response[:80]}")
            skipped += 1

        # Polite delay to avoid overwhelming Ollama
        time.sleep(0.5)

    # Save dataset
    output_path = Path(OUTPUT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    logger.success(f"\nGenerated {len(dataset)} Q&A pairs ({skipped} skipped).")
    logger.success(f"Saved to '{OUTPUT_PATH}'.")
    logger.info("Review the file before running RAGAS evaluation.")
    logger.info(
        "Add or remove entries as needed. Quality of eval data = quality of your scores."
    )


if __name__ == "__main__":
    generate_dataset()
