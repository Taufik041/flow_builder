import os
import uuid
from pathlib import Path

from chunker import chunk_markdown
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "wa_flows_knowledge"
KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", "/knowledge")

model = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(url=QDRANT_URL)


def ensure_collection():
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )


def index_all() -> dict:
    ensure_collection()
    knowledge_path = Path(KNOWLEDGE_DIR)
    all_chunks = []

    # knowledge base markdown
    kb_file = knowledge_path / "whatsapp_flows_knowledge_base.md"
    if kb_file.exists():
        all_chunks.extend(
            chunk_markdown(kb_file.read_text(encoding="utf-8"), "knowledge_base")
        )

    # scraped meta docs
    meta_docs_dir = knowledge_path / "meta_docs"
    if meta_docs_dir.exists():
        for f in meta_docs_dir.iterdir():
            if f.suffix == ".md":
                all_chunks.extend(
                    chunk_markdown(f.read_text(encoding="utf-8"), f"meta_docs/{f.stem}")
                )

    if not all_chunks:
        return {"indexed": 0}

    texts = [c["text"] for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=False)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding.tolist(),
            payload=chunk,
        )
        for chunk, embedding in zip(all_chunks, embeddings, strict=False)
    ]

    # clear and reindex
    client.delete_collection(COLLECTION_NAME)
    ensure_collection()
    client.upsert(collection_name=COLLECTION_NAME, points=points)

    return {"indexed": len(points)}
