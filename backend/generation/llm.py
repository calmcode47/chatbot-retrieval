"""
LLM interface — supports Groq (cloud, free) and Ollama (local).

Priority:
  1. If GROQ_API_KEY env var is set → use Groq (recommended for Railway/cloud)
  2. Otherwise → use Ollama (local dev / self-hosted)
"""

import os
from loguru import logger


def get_llm(
    model: str = None,
    temperature: float = 0.1,
    # Ollama-only params (ignored when using Groq)
    base_url: str = None,
    num_ctx: int = 4096,
):
    """
    Return an LLM instance.

    Cloud deployment (Railway): set GROQ_API_KEY → uses Groq API (free tier).
    Local deployment: leave GROQ_API_KEY unset → uses Ollama on localhost.
    """
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()

    if groq_api_key:
        from langchain_groq import ChatGroq

        groq_model = model or os.getenv("GROQ_MODEL", "llama3-8b-8192")
        logger.info(f"Using Groq LLM: model={groq_model}")
        return ChatGroq(
            api_key=groq_api_key,
            model=groq_model,
            temperature=temperature,
        )

    else:
        from langchain_ollama import ChatOllama

        ollama_model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        ollama_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        logger.info(f"Using Ollama LLM: model={ollama_model}, url={ollama_url}")

        llm = ChatOllama(
            model=ollama_model,
            base_url=ollama_url,
            temperature=temperature,
            num_ctx=num_ctx,
            num_predict=-1,
            request_timeout=120.0,
        )

        # Quick health check for local Ollama
        try:
            test = llm.invoke("Respond with exactly: OK")
            logger.info(f"Ollama ready. Health: {test.content[:20]}")
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}. Is 'ollama serve' running?")
            raise

        return llm


# ---------------------------------------------------------------------------
# Backward-compatibility alias so existing callers keep working unchanged
# ---------------------------------------------------------------------------
def get_ollama_llm(
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.1,
    streaming: bool = False,
    num_ctx: int = 4096,
):
    """Backward-compat wrapper — delegates to get_llm()."""
    return get_llm(model=model, temperature=temperature, base_url=base_url, num_ctx=num_ctx)
