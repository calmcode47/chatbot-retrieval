# backend/pipeline/context_window.py
"""
Dynamic context window manager for Ollama LLM calls.

Responsibilities:
  1. Count tokens accurately using tiktoken
  2. Trim retrieved chunks to fit within the model's context window
  3. Set Ollama's num_ctx dynamically based on actual prompt size
  4. Log when trimming occurs so you know the retrieval is being constrained

Usage:
    manager = ContextWindowManager(model_name="llama3.2:3b", num_ctx=4096)
    fitted_chunks, stats = manager.fit_chunks(retrieved_chunks)
    # stats tells you how many chunks were dropped and why
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import tiktoken
from loguru import logger

# Default context window sizes for Ollama models.
# These are the num_ctx values used unless overridden in config.yaml.
# Source: Ollama model cards + empirical testing on M4.
MODEL_CONTEXT_DEFAULTS: Dict[str, int] = {
    "llama3.2:3b": 8192,
    "llama3.1:8b": 8192,
    "mistral:7b": 32768,
    "phi3:mini": 8192,
    "phi3:medium": 8192,
}

FALLBACK_CONTEXT_LIMIT = 4096  # Conservative fallback for unknown models


class ContextWindowManager:
    """
    Measures and manages token usage to prevent context window overflow.

    Designed to sit between the retriever and the LLM call:
        chunks = retriever.search(query, top_k=20)
        fitted, stats = manager.fit_chunks(chunks)
        # Pass fitted to context builder, stats to API response telemetry
    """

    def __init__(
        self,
        model_name: str = "llama3.2:3b",
        num_ctx: int = None,
        reserved_system_tokens: int = 350,
        reserved_answer_tokens: int = 1024,
        reserved_query_tokens: int = 150,
        reserved_history_tokens: int = 250,
    ):
        """
        Args:
            model_name:               Ollama model name — used for default num_ctx lookup
            num_ctx:                  Explicit context window override (tokens). If None,
                                      inferred from MODEL_CONTEXT_DEFAULTS.
            reserved_system_tokens:   Tokens reserved for your RAG system prompt
            reserved_answer_tokens:   Tokens reserved for the LLM's answer (max_tokens)
            reserved_query_tokens:    Tokens reserved for the user's question
            reserved_history_tokens:  Tokens reserved for conversation history turns
        """
        self.model_name = model_name
        self.num_ctx = num_ctx or MODEL_CONTEXT_DEFAULTS.get(
            model_name, FALLBACK_CONTEXT_LIMIT
        )

        self._reserved = (
            reserved_system_tokens
            + reserved_answer_tokens
            + reserved_query_tokens
            + reserved_history_tokens
        )
        self.context_budget = self.num_ctx - self._reserved

        # tiktoken cl100k_base is used by GPT-4 and is a good approximation
        # for Llama/Mistral family models (slight undercount, safe side)
        try:
            self._enc = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._enc = None
            logger.warning(
                "tiktoken not available — using character approximation for token counting"
            )

        logger.debug(
            f"ContextWindowManager: model={model_name}, num_ctx={self.num_ctx}, "
            f"reserved={self._reserved}, context_budget={self.context_budget} tokens"
        )

    # ── Token counting ─────────────────────────────────────────────────

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a string.
        Uses tiktoken when available, falls back to character approximation.
        """
        if not text:
            return 0
        if self._enc:
            return len(self._enc.encode(text))
        # Approximation: ~4 chars per token (conservative for English)
        return max(1, len(text) // 4)

    def count_chunks_tokens(self, chunks: List[Dict[str, Any]]) -> int:
        """Total tokens across all chunk documents."""
        return sum(self.count_tokens(c.get("document", "")) for c in chunks)

    # ── Core fitting logic ─────────────────────────────────────────────

    def fit_chunks(
        self,
        chunks: List[Dict[str, Any]],
        query: str = "",
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Trim chunk list to fit within the context budget.

        Chunks are assumed to be sorted by relevance (best first).
        Trimming removes from the tail — lowest relevance chunks go first.

        Args:
            chunks: Retrieved and re-ranked chunks (best-first order)
            query:  The current query (for dynamic query-length accounting)

        Returns:
            (fitted_chunks, stats_dict)

            stats_dict keys:
                original_count    — chunks before fitting
                fitted_count      — chunks after fitting
                dropped_count     — how many were removed
                tokens_used       — tokens consumed by fitted chunks
                tokens_budget     — total available for context
                utilization_pct   — percentage of budget used
                overflow_prevented — True if any chunks were dropped
        """
        # Dynamic query accounting — actual query may be longer than reserved
        query_tokens = self.count_tokens(query)
        effective_budget = self.context_budget
        if query_tokens > 150:  # Exceeds our reserved estimate
            effective_budget -= query_tokens - 150

        if effective_budget <= 0:
            logger.warning(
                "Context budget exhausted by query alone — no chunks can fit"
            )
            return [], self._make_stats(chunks, [], 0, self.context_budget)

        fitted = []
        used_tokens = 0

        for chunk in chunks:
            chunk_tokens = self.count_tokens(chunk.get("document", ""))

            if used_tokens + chunk_tokens > effective_budget:
                # This chunk would overflow — stop here
                break

            fitted.append(chunk)
            used_tokens += chunk_tokens

        stats = self._make_stats(chunks, fitted, used_tokens, effective_budget)

        if stats["dropped_count"] > 0:
            logger.warning(
                f"Context window: dropped {stats['dropped_count']} chunk(s) "
                f"to fit within {self.num_ctx}-token window. "
                f"Used {used_tokens}/{effective_budget} context tokens."
            )
        else:
            logger.debug(
                f"Context window: all {len(fitted)} chunks fit "
                f"({used_tokens}/{effective_budget} tokens, "
                f"{stats['utilization_pct']}% utilization)"
            )

        return fitted, stats

    def _make_stats(
        self,
        original: List,
        fitted: List,
        used_tokens: int,
        budget: int,
    ) -> Dict[str, Any]:
        dropped = len(original) - len(fitted)
        return {
            "original_count": len(original),
            "fitted_count": len(fitted),
            "dropped_count": dropped,
            "tokens_used": used_tokens,
            "tokens_budget": budget,
            "tokens_total_window": self.num_ctx,
            "utilization_pct": (
                round(used_tokens / budget * 100, 1) if budget > 0 else 0.0
            ),
            "overflow_prevented": dropped > 0,
        }

    # ── Ollama num_ctx recommendation ──────────────────────────────────

    def recommended_num_ctx(self, chunks: List[Dict[str, Any]], query: str = "") -> int:
        """
        Calculate the minimum num_ctx needed to fit all chunks without trimming.

        Use this to dynamically set Ollama's num_ctx if you want to expand
        the window instead of trimming chunks.

        Returns a value rounded up to the nearest 1024 for Ollama compatibility.
        """
        context_tokens = self.count_chunks_tokens(chunks)
        query_tokens = self.count_tokens(query)
        total_needed = context_tokens + query_tokens + self._reserved

        # Round up to nearest 1024
        rounded = ((total_needed + 1023) // 1024) * 1024
        return min(
            rounded, MODEL_CONTEXT_DEFAULTS.get(self.model_name, FALLBACK_CONTEXT_LIMIT)
        )
