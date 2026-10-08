from app.rag.retriever import Retriever


class RAGService:
    """Service layer for SolarIQ retrieval."""

    def __init__(self):
        self.retriever = Retriever()

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> dict:
        """Retrieve relevant evidence for a user query."""

        results = self.retriever.search(
            query=query,
            top_k=top_k,
        )

        return {
            "query": query,
            "results": results,
        }