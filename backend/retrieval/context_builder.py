"""
Assembles retrieved chunks into a structured context string for the LLM prompt.
"""

from typing import Any, Dict, List


class ContextBuilder:
    """
    Takes search results from the vector store and formats them
    into a clean context block that the LLM can reason over.
    """

    def build(
        self,
        results: List[Dict[str, Any]],
        score_threshold: float = 0.3,
    ) -> tuple[str, List[Dict]]:
        """
        Format retrieved chunks into a context string.

        Args:
            results: List of search hits from VectorStore.search()
            score_threshold: Minimum similarity score to include

        Returns:
            (context_string, used_sources)
        """
        # Filter out low-relevance chunks
        filtered = [r for r in results if r["score"] >= score_threshold]

        if not filtered:
            return "No relevant context found.", []

        context_parts = []
        sources = []

        for i, result in enumerate(filtered, 1):
            source_file = result["metadata"].get("source_file", "unknown")
            page = result["metadata"].get("page", "?")
            score = result["score"]

            # Format each chunk clearly for the LLM
            context_parts.append(
                f"[Source {i}: {source_file}, Page {page} | Relevance: {score:.2f}]\n"
                f"{result['document']}"
            )

            sources.append(
                {
                    "source_file": source_file,
                    "page": page,
                    "score": score,
                    "excerpt": result["document"][:200] + "...",
                }
            )

        context_string = "\n\n---\n\n".join(context_parts)
        return context_string, sources
