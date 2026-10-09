from app.rag.ingestion import extract_document


def test_extract_txt_document():
    documents = extract_document("data/raw/solar_knowledge.txt")

    assert len(documents) == 1
    assert documents[0]["source"] == "solar_knowledge.txt"
    assert documents[0]["page"] is None
    assert "Solar photovoltaic systems" in documents[0]["text"]