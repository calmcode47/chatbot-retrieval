"""
LLM interface — supports Groq (cloud, free), self-contained SLM (Hugging Face), and Ollama (local).

Priority:
  1. If GROQ_API_KEY env var is set → use Groq (recommended for cloud)
  2. If USE_OLLAMA env var is set to 'true' → use Ollama (requires local/external ollama)
  3. Otherwise (default) → use self-contained HuggingFace model (Qwen2.5-0.5B-Instruct)
"""

import os
from loguru import logger

# Singleton cache for local Hugging Face SLM to avoid reloading model weights
_local_slm_instance = None


def get_llm(
    model: str = None,
    temperature: float = 0.1,
    # Ollama-only params (ignored when using Groq/HuggingFace)
    base_url: str = None,
    num_ctx: int = 4096,
):
    """
    Return an LLM instance.

    1. If GROQ_API_KEY is configured → uses Groq API (free tier).
    2. If USE_OLLAMA=true is configured → uses Ollama.
    3. Default → downloads and runs a local Qwen2.5-0.5B-Instruct model inside Python.
    """
    global _local_slm_instance
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    use_ollama = os.getenv("USE_OLLAMA", "").strip().lower() == "true"

    if groq_api_key:
        from langchain_groq import ChatGroq

        groq_model = model or os.getenv("GROQ_MODEL", "llama3-8b-8192")
        logger.info(f"Using Groq LLM: model={groq_model}")
        return ChatGroq(
            api_key=groq_api_key,
            model=groq_model,
            temperature=temperature,
        )

    elif use_ollama:
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
            logger.warning(f"Ollama connection check failed: {e}. Startup will continue, but LLM calls may fail unless GROQ_API_KEY is configured.")

        return llm

    else:
        # Default: Use self-contained local SLM running inside Python via HuggingFace
        if _local_slm_instance is None:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            from langchain_huggingface import ChatHuggingFace
            from langchain_community.llms import HuggingFacePipeline
            import torch

            model_id = model or os.getenv("LOCAL_SLM_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
            
            # If fine-tuned model path exists, prioritize it
            if os.path.exists("./models/fine-tuned-slm"):
                model_id = "./models/fine-tuned-slm"
                logger.info(f"Loading custom fine-tuned SLM from {model_id}...")
            else:
                logger.info(f"Loading self-contained local SLM: {model_id}...")

            # Auto-detect device (cuda, mps, cpu)
            device = "cpu"
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"

            logger.info(f"Loading SLM on device: {device}")

            tokenizer = AutoTokenizer.from_pretrained(model_id)
            # Use float16 on GPU, float32 on CPU
            torch_dtype = torch.float16 if device in ["cuda", "mps"] else torch.float32
            
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch_dtype,
                device_map="auto" if device in ["cuda", "mps"] else None,
            )
            if device == "cpu":
                model = model.to("cpu")

            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512,
                temperature=temperature,
                do_sample=temperature > 0.0,
            )
            
            hf_llm = HuggingFacePipeline(pipeline=pipe)
            _local_slm_instance = ChatHuggingFace(llm=hf_llm)
            logger.success("Self-contained local SLM loaded successfully.")

        return _local_slm_instance


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
