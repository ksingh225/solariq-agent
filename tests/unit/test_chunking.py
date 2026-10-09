from app.rag.chunking import chunk_documents


def test_chunk_documents_preserves_metadata():
    documents = [
        {
            "text": "Solar irradiance affects photovoltaic generation.",
            "source": "solar_knowledge.txt",
            "page": None,
        }
    ]

    chunks = chunk_documents(documents)

    assert len(chunks) == 1
    assert chunks[0]["source"] == "solar_knowledge.txt"
    assert chunks[0]["page"] is None
    assert chunks[0]["chunk_id"] == 0
    assert "Solar irradiance" in chunks[0]["text"]