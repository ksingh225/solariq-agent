from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


COLLECTION_NAME = "solariq_knowledge"
VECTOR_SIZE = 384


class VectorStore:
    """Qdrant vector store for SolarIQ knowledge."""

    def __init__(self, path: str = "data/qdrant"):
        self.client = QdrantClient(path=path)

    def create_collection(self) -> None:
        """Create the SolarIQ knowledge collection if it does not exist."""

        collections = self.client.get_collections().collections

        if COLLECTION_NAME not in [collection.name for collection in collections]:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )

    def upsert(
        self,
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> None:
        """Store vectors and their metadata in Qdrant."""

        points = [
            PointStruct(
                id=index,
                vector=vector,
                payload=payload,
            )
            for index, (vector, payload) in enumerate(
                zip(vectors, payloads)
            )
        ]

        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )

    def count(self) -> int:
        """Return the number of stored vectors."""

        result = self.client.count(
            collection_name=COLLECTION_NAME,
        )

        return result.count