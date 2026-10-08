def chunk_documents(
    documents: list[dict],
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[dict]:
    """Split documents into paragraph-aware overlapping chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and less than chunk_size")

    chunks = []

    for document in documents:
        paragraphs = [
            paragraph.strip()
            for paragraph in document["text"].split("\n\n")
            if paragraph.strip()
        ]

        current_chunk = ""

        for paragraph in paragraphs:
            candidate = (
                f"{current_chunk}\n\n{paragraph}"
                if current_chunk
                else paragraph
            )

            if len(candidate) <= chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(
                        {
                            "text": current_chunk,
                            "source": document["source"],
                            "page": document["page"],
                            "chunk_id": len(chunks),
                        }
                    )

                current_chunk = paragraph

        if current_chunk:
            chunks.append(
                {
                    "text": current_chunk,
                    "source": document["source"],
                    "page": document["page"],
                    "chunk_id": len(chunks),
                }
            )

    return chunks