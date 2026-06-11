import os

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "wa_flows_knowledge"

model = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(url=QDRANT_URL)


def retrieve(query: str, top_k: int = 8) -> list[dict]:
    query_vector = model.encode(query).tolist()
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
    )
    return [
        {
            "text": point.payload["text"],
            "source": point.payload["source"],
            "title": point.payload["title"],
            "score": point.score,
        }
        for point in results.points
    ]
