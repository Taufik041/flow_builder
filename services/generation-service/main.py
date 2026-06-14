import json
import os
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from generator import stream_generation
from prompt_builder import build_system_prompt, build_user_message
from pydantic import BaseModel

load_dotenv()

RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag-service:8002")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)


class GenerateRequest(BaseModel):
    user_message: str
    extracted_text: str | None = None
    chat_history: list[dict] = []
    version: str = "7.3"
    top_k: int = 8
    model: str = "gpt-4o"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(body: GenerateRequest):
    # retrieve relevant chunks from RAG
    async with httpx.AsyncClient() as client:
        rag_response = await client.post(
            f"{RAG_SERVICE_URL}/retrieve",
            json={"query": body.user_message, "top_k": body.top_k},
            timeout=30,
        )
    chunks = rag_response.json().get("chunks", [])
    chunks = rag_response.json().get("chunks", [])
    for _c in chunks:
        pass

    # inject version preference into the user message
    user_msg = body.user_message
    if body.version == "7.1":
        user_msg = f"[Use version 7.1] {user_msg}"

    system_prompt = build_system_prompt(chunks)
    user_message = build_user_message(user_msg, body.extracted_text)

    # in main.py generate endpoint, after building prompts:
    async def event_stream():
        async for token in stream_generation(
            system_prompt, user_message, body.chat_history, body.model
        ):
            # SSE format
            data = json.dumps({"token": token})
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
