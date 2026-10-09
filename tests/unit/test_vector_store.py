from app.rag.vector_store import VectorStore


def test_vector_store_upsert_and_count(tmp_path):
    store = VectorStore(path=str(tmp_path / "qdrant"))

    store.create_collection()

    vectors = [[0.1] * 384]
    payloads = [
        {
            "text": "Solar irradiance affects generation.",
            "source": "test.txt",
            "page": None,
            "chunk_id": 0,
        }
    ]

    store.upsert(vectors, payloads)

    assert store.count() == 1

    store.client.close()