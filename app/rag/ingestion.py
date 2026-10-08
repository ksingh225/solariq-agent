from pathlib import Path

import pymupdf


def extract_text_from_txt(path: str) -> list[dict]:
    """Extract text from a plain-text knowledge document."""
    file_path = Path(path)

    text = file_path.read_text(encoding="utf-8")

    if not text.strip():
        return []

    return [
        {
            "text": text,
            "source": file_path.name,
            "page": None,
        }
    ]


def extract_text_from_pdf(path: str) -> list[dict]:
    """Extract text from each page of a PDF."""
    file_path = Path(path)
    pages = []

    document = pymupdf.open(file_path)

    for page_number, page in enumerate(document, start=1):
        text = page.get_text("text")

        if text.strip():
            pages.append(
                {
                    "text": text,
                    "source": file_path.name,
                    "page": page_number,
                }
            )

    document.close()

    return pages


def extract_document(path: str) -> list[dict]:
    """Extract text based on the document type."""
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return extract_text_from_txt(path)

    if suffix == ".pdf":
        return extract_text_from_pdf(path)

    raise ValueError(
        f"Unsupported document type: {suffix}. "
        "Supported types are .txt and .pdf."
    )
