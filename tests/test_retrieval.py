"""
Unit tests for the retrieval pipeline.
"""

import pytest
from ingestion.embedder import EmbeddingService
from retrieval.vector_store import VectorStore
from retrieval.context_builder import ContextBuilder


@pytest.fixture(scope="module")
def embedder():
    return EmbeddingService()


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("chroma")
    return VectorStore(persist_directory=str(tmp), collection_name="test_collection")


def test_embedding_dimension(embedder):
    vec = embedder.embed("Hello, world!")
    assert len(vec) == 768, f"Expected 768-dim vector, got {len(vec)}"


def test_embedding_normalized(embedder):
    import math
    vec = embedder.embed("Test sentence")
    magnitude = math.sqrt(sum(v**2 for v in vec))
    assert abs(magnitude - 1.0) < 0.01, "Embedding should be normalized (unit vector)"


def test_vector_store_add_and_search(embedder, store):
    texts = ["The sky is blue.", "Water is wet.", "Fire is hot."]
    embeddings = embedder.embed_batch(texts)
    ids = ["doc_0", "doc_1", "doc_2"]
    metadatas = [{"source_file": "test.txt"} for _ in texts]

    store.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    assert store.count == 3

    query_vec = embedder.embed("What color is the sky?")
    results = store.search(query_vec, top_k=1)

    assert len(results) == 1
    assert "blue" in results[0]["document"].lower()
    assert results[0]["score"] > 0.5


def test_context_builder():
    builder = ContextBuilder()
    mock_results = [
        {
            "document": "The refund policy is 30 days.",
            "metadata": {"source_file": "policy.pdf", "page": 1},
            "score": 0.87,
        },
        {
            "document": "Contact us at support@company.com.",
            "metadata": {"source_file": "policy.pdf", "page": 2},
            "score": 0.21,  # Below threshold
        },
    ]
    context, sources = builder.build(mock_results, score_threshold=0.3)
    assert "refund policy" in context
    assert len(sources) == 1  # Second chunk filtered out


def test_context_builder_empty():
    builder = ContextBuilder()
    context, sources = builder.build([], score_threshold=0.3)
    assert "No relevant context" in context
    assert sources == []


def test_reranker():
    from retrieval.reranker import CrossEncoderReranker
    reranker = CrossEncoderReranker()

    query = "What is the refund policy?"
    mock_results = [
        {"document": "Our office is located in SF.", "metadata": {"source_file": "office.txt"}, "score": 0.5},
        {"document": "Refunds are processed within 30 days.", "metadata": {"source_file": "refund.txt"}, "score": 0.4},
    ]

    reranked = reranker.rerank(query, mock_results, top_k=2)
    assert len(reranked) == 2
    # The refund document should be re-ranked to the top (index 0)
    assert "refund" in reranked[0]["document"].lower()
    assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]


def test_conversational_chain_condense():
    from unittest.mock import MagicMock, patch
    from pipeline.conversational_chain import ConversationalRAGChain

    # Mock Ollama generation function
    with patch("pipeline.conversational_chain.get_ollama_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        # Mock Ollama invoke return value
        mock_response = MagicMock()
        mock_response.content = "What is the refund policy for damaged items?"
        mock_llm.invoke.return_value = mock_response

        # Initialize chain (will use mocked get_ollama_llm)
        chain = ConversationalRAGChain(
            embedder=MagicMock(),
            vector_store=MagicMock(),
            model_name="mock-model",
            use_reranker=False,
        )

        chat_history = [("What is the refund policy?", "You can return items within 30 days.")]
        condensed = chain._condense_question("What about damaged items?", chat_history)

        assert condensed == "What is the refund policy for damaged items?"
        mock_llm.invoke.assert_called_once()
