"""
Local LLM interface via Ollama.
"""

from langchain_ollama import ChatOllama
from loguru import logger


def get_ollama_llm(
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.1,
    streaming: bool = True,
    num_ctx: int = 4096,
) -> ChatOllama:
    """
    Returns a ChatOllama instance with explicit context window configuration.

    Always set num_ctx explicitly — never rely on Ollama's default.
    Ollama's default num_ctx varies by model version and can be as low as 2048.
    """
    logger.info(f"Initializing Ollama: model={model}, num_ctx={num_ctx}")

    llm = ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
        streaming=streaming,
        num_ctx=num_ctx,
    )

    # Quick health check
    try:
        test_response = llm.invoke("Respond with exactly: OK")
        logger.info(f"Ollama LLM ready. Health check: {test_response.content[:20]}")
    except Exception as e:
        logger.error(f"Ollama connection failed: {e}. Is 'ollama serve' running?")
        raise

    return llm
