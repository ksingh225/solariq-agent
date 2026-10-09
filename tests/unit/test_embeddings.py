from app.rag.embeddings import EmbeddingModel


def test_embedding_dimension():
    model = EmbeddingModel()

    vectors = model.embed_texts(
        ["Solar irradiance affects photovoltaic generation."]
    )

    assert len(vectors) == 1
    assert len(vectors[0]) == 384