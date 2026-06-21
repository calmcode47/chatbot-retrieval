"""
Full RAG pipeline using LangChain.
Wires: query embedding → vector search → context building → LLM generation.
"""

from typing import Dict, Any, List
from loguru import logger

from ingestion.embedder import EmbeddingService
from retrieval.vector_store import VectorStore
from retrieval.context_builder import ContextBuilder
from retrieval.reranker import CrossEncoderReranker
from generation.llm import get_ollama_llm
from generation.prompt_templates import get_rag_prompt


class RAGChain:
    def __init__(
        self,
        embedder: EmbeddingService = None,
        vector_store: VectorStore = None,
        model_name: str = "llama3.2:3b",
        top_k: int = 5,
        score_threshold: float = 0.3,
        use_reranker: bool = True,          # NEW PARAMETER
        reranker_candidates: int = 20,       # NEW PARAMETER — fetch 20, rerank to top_k
    ):
        self.embedder = embedder or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        self.context_builder = ContextBuilder()
        self.llm = get_ollama_llm(model=model_name)
        self.prompt = get_rag_prompt()
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.use_reranker = use_reranker
        self.reranker_candidates = reranker_candidates

        # Only load cross-encoder if reranking is enabled
        if self.use_reranker:
            self.reranker = CrossEncoderReranker()
        else:
            self.reranker = None

        logger.info(f"RAGChain initialized. Reranker: {'ON' if use_reranker else 'OFF'}")

    def query(self, question: str) -> Dict[str, Any]:
        """Run a full RAG query with optional cross-encoder reranking."""
        logger.info(f"Processing query: '{question[:80]}'")

        # Step 1: Embed the query
        query_embedding = self.embedder.embed(question)

        # Step 2: Retrieve candidates
        # With reranker ON: fetch more candidates (20) for reranking
        # With reranker OFF: fetch only top_k directly
        fetch_k = self.reranker_candidates if self.use_reranker else self.top_k
        search_results = self.vector_store.search(query_embedding, top_k=fetch_k)

        # Step 3: Rerank if enabled
        if self.use_reranker and search_results:
            search_results = self.reranker.rerank(
                query=question,
                results=search_results,
                top_k=self.top_k,
            )

        # Steps 4–6: Context → Prompt → LLM
        context, sources = self.context_builder.build(search_results, self.score_threshold)
        messages = self.prompt.format_messages(context=context, question=question)
        response = self.llm.invoke(messages)

        return {
            "question": question,
            "answer": response.content,
            "sources": sources,
            "retrieval_scores": [r["score"] for r in search_results],
            "rerank_scores": [r.get("rerank_score") for r in search_results] if self.use_reranker else [],
            "chunks_used": len(sources),
            "reranker_used": self.use_reranker,
        }

    def stream_query(self, question: str):
        """
        Generator version — yields answer tokens as they're produced.
        Use this for real-time streaming in the API/UI.
        """
        query_embedding = self.embedder.embed(question)
        
        fetch_k = self.reranker_candidates if self.use_reranker else self.top_k
        search_results = self.vector_store.search(query_embedding, top_k=fetch_k)
        
        if search_results and self.use_reranker and self.reranker:
            search_results = self.reranker.rerank(
                query=question,
                results=search_results,
                top_k=self.top_k,
            )

        context, sources = self.context_builder.build(search_results, self.score_threshold)
        messages = self.prompt.format_messages(context=context, question=question)

        # Yield sources first (metadata)
        yield {"type": "sources", "sources": sources}

        # Then stream the answer tokens
        for chunk in self.llm.stream(messages):
            yield {"type": "token", "content": chunk.content}


# Quick test
if __name__ == "__main__":
    chain = RAGChain()
    result = chain.query("What documents do you have?")
    print(f"\nAnswer: {result['answer']}")
    print(f"Sources: {result['sources']}")
