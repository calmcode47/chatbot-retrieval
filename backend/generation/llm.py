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
) -> ChatOllama:
    """
    Returns a LangChain-compatible Ollama LLM.

    Args:
        model: Ollama model name (e.g., 'llama3.2:3b', 'mistral:7b')
        base_url: Ollama server address
        temperature: 0.0 = deterministic, 1.0 = creative
        streaming: Enable token streaming

    Returns:
        ChatOllama instance
    """
    logger.info(f"Initializing Ollama LLM: {model}")

    llm = ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
        streaming=streaming,
    )

    # Quick health check
    try:
        test_response = llm.invoke("Respond with exactly: OK")
        logger.info(f"Ollama LLM ready. Health check: {test_response.content[:20]}")
    except Exception as e:
        logger.error(f"Ollama connection failed: {e}. Is 'ollama serve' running?")
        raise

    return llm
