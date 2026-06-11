from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from indexer import KNOWLEDGE_DIR, index_all
from pydantic import BaseModel
from retriever import retrieve

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
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
