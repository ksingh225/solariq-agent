from unittest.mock import MagicMock, patch

from app.rag.retriever import Retriever


@patch("app.rag.retriever.VectorStore")
@patch("app.rag.retriever.EmbeddingModel")
def test_retriever_returns_relevant_results(
    mock_embedding_model,
    mock_vector_store,
):
    # Simulate a query embedding
    query_vector = [0.1] * 384
    mock_embedding_model.return_value.embed_query.return_value = query_vector

    # Simulate one Qdrant search result
    result = MagicMock()
    result.payload = {
        "text": "Cloud cover can reduce solar generation.",
        "source": "solar_knowledge.txt",
        "page": None,
    }
    result.score = 0.85

    mock_vector_store.return_value.client.query_points.return_value.points = [
        result
    ]

    retriever = Retriever()

    results = retriever.search(
        query="What reduces solar generation?",
        top_k=3,
    )

    assert len(results) == 1
    assert results[0]["source"] == "solar_knowledge.txt"
    assert results[0]["score"] == 0.85
    assert "Cloud cover" in results[0]["text"]

    mock_vector_store.return_value.client.query_points.assert_called_once_with(
        collection_name="solariq_knowledge",
        query=query_vector,
        limit=3,
    )