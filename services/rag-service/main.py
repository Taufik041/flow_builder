from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from indexer import COLLECTION_NAME, KNOWLEDGE_DIR, client, index_all
from pydantic import BaseModel
from retriever import retrieve

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        collections = [c.name for c in client.get_collections().collections]
        count = (
            client.count(COLLECTION_NAME).count if COLLECTION_NAME in collections else 0
        )
    except Exception:
        count = 0
    if count == 0:
        print("[startup] empty index — running index_all()")  # noqa: T201
        print(index_all())  # noqa: T201
    else:
        print(f"[startup] index has {count} points, skipping")  # noqa: T201
    yield


app = FastAPI(lifespan=lifespan)


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 8


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/index")
async def index():
    return index_all()


@app.post("/retrieve")
async def retrieve_chunks(body: RetrieveRequest):
    chunks = retrieve(body.query, body.top_k)
    return {"chunks": chunks}


@app.get("/examples")
async def get_examples():
    examples_dir = Path(KNOWLEDGE_DIR) / "examples"
    examples = {}
    if examples_dir.exists():
        for f in examples_dir.iterdir():
            if f.suffix in (".json", ".py"):
                examples[f.name] = f.read_text(encoding="utf-8")
    return examples
