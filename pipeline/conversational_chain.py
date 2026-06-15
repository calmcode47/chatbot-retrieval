# pipeline/conversational_chain.py
"""
Multi-turn conversational RAG pipeline.

Extends RAGChain with conversation memory by:
1. Condensing follow-up questions into standalone questions
2. Maintaining a rolling window of previous turns
3. Passing condensed questions to the existing retrieval pipeline
"""

from typing import List, Dict, Any, Tuple
from loguru import logger

from ingestion.embedder import EmbeddingService
from retrieval.vector_store import VectorStore
from retrieval.reranker import CrossEncoderReranker
from retrieval.context_builder import ContextBuilder
from generation.llm import get_ollama_llm
from generation.prompt_templates import get_rag_prompt, CONDENSE_QUESTION_PROMPT


class ConversationalRAGChain:
    """
    Stateful RAG pipeline with conversation history.
    
    Each session should maintain its own instance (or pass history externally).
    For the API, history is passed per-request (stateless server, stateful client).
    """

    def __init__(
        self,
        embedder: EmbeddingService = None,
        vector_store: VectorStore = None,
        model_name: str = "llama3.2:3b",
        top_k: int = 5,
        score_threshold: float = 0.3,
        use_reranker: bool = True,
        reranker_candidates: int = 20,
        max_history_turns: int = 5,
    ):
        self.embedder = embedder or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        self.context_builder = ContextBuilder()
        self.llm = get_ollama_llm(model=model_name)
        self.rag_prompt = get_rag_prompt()
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.max_history_turns = max_history_turns

        if use_reranker:
            self.reranker = CrossEncoderReranker()
        else:
            self.reranker = None

        logger.info("ConversationalRAGChain initialized.")

    def _condense_question(
        self, question: str, chat_history: List[Tuple[str, str]]
    ) -> str:
        """
        If there is chat history, rewrite the follow-up question
        into a standalone question using the LLM.
        
        Args:
            question:     Current user message
            chat_history: List of (user_message, assistant_response) tuples
        
        Returns:
            A standalone question (or the original if no history exists)
        """
        if not chat_history:
            return question  # No history — question is already standalone

        # Format history as a readable string
        history_text = "\n".join(
            [f"Human: {h}\nAssistant: {a}" for h, a in chat_history[-self.max_history_turns:]]
        )

        # Use the condense prompt to rewrite the question
        condensed_prompt = CONDENSE_QUESTION_PROMPT.format(
            chat_history=history_text,
            question=question,
        )

        response = self.llm.invoke(condensed_prompt)
        condensed = response.content.strip()

        logger.debug(f"Original question:  '{question}'")
        logger.debug(f"Condensed question: '{condensed}'")

        return condensed

    def query(
        self,
        question: str,
        chat_history: List[Tuple[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Run a conversational RAG query.

        Args:
            question:     Current user message
            chat_history: List of (user_question, assistant_answer) tuples
                          from previous turns. Pass [] or None for first turn.

        Returns:
            Dict with answer, sources, condensed_question, and all scores.
        """
        if chat_history is None:
            chat_history = []

        # Step 1: Condense the follow-up question if history exists
        standalone_question = self._condense_question(question, chat_history)

        # Step 2: Embed the standalone question
        query_embedding = self.embedder.embed(standalone_question)

        # Step 3: Retrieve
        fetch_k = 20 if self.reranker else self.top_k
        search_results = self.vector_store.search(query_embedding, top_k=fetch_k)

        # Step 4: Rerank
        if self.reranker and search_results:
            search_results = self.reranker.rerank(
                query=standalone_question,
                results=search_results,
                top_k=self.top_k,
            )

        # Step 5: Build context and generate answer
        context, sources = self.context_builder.build(search_results, self.score_threshold)
        messages = self.rag_prompt.format_messages(context=context, question=standalone_question)
        response = self.llm.invoke(messages)

        return {
            "question": question,
            "condensed_question": standalone_question,
            "answer": response.content,
            "sources": sources,
            "chunks_used": len(sources),
            "history_turns_used": len(chat_history),
        }
