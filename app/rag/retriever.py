from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import COLLECTION_NAME, VectorStore


class Retriever:
    """Retrieve relevant SolarIQ knowledge from Qdrant."""

    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore()

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:
        """Retrieve the most relevant knowledge chunks."""

        query_vector = self.embedding_model.embed_query(query)

        results = self.vector_store.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
        ).points

        return [
            {
                "text": result.payload["text"],
                "source": result.payload["source"],
                "page": result.payload["page"],
                "score": result.score,
            }
            for result in results
        ]