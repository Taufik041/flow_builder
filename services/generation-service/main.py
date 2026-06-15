import json
import os
from contextlib import asynccontextmanager

import aisensy_client
import flow_lifecycle as fl
import httpx
from dotenv import load_dotenv
from fastapi import Body, FastAPI
from fastapi.responses import StreamingResponse
from generator import stream_generation
from prompt_builder import (
    build_backend_user_message,
    build_system_prompt,
    build_user_message,
)
from pydantic import BaseModel

load_dotenv()

RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag-service:8002")
MAX_REPAIR_ATTEMPTS = int(
    os.getenv("MAX_REPAIR_ATTEMPTS", "4")
)  # JSON tries incl. first


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
    aisensy_flow_id: str | None = None
    flow_name: str | None = None
    flow_category: str | None = None


def _sse(obj: dict | str) -> str:
    if obj == "[DONE]":
        return "data: [DONE]\n\n"
    return f"data: {json.dumps(obj)}\n\n"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(body: GenerateRequest):
    async with httpx.AsyncClient() as client:
        rag_response = await client.post(
            f"{RAG_SERVICE_URL}/retrieve",
            json={"query": body.user_message, "top_k": body.top_k},
            timeout=30,
        )
    if rag_response.status_code != 200:
        chunks = []  # degrade gracefully if RAG is down
    else:
        chunks = rag_response.json().get("chunks", [])

    user_msg = body.user_message
    if body.version == "7.1":
        user_msg = f"[Use version 7.1] {user_msg}"

    json_system_prompt = build_system_prompt(chunks, phase="json")
    backend_system_prompt = build_system_prompt(chunks, phase="backend")

    async def event_stream():
        flow_id = body.aisensy_flow_id
        attempt = 0
        final_flow_json: dict | None = None
        current_user_message = build_user_message(user_msg, body.extracted_text)

        # =====================================================================
        # PHASE 1 — JSON only, iterate against Meta's validator
        # =====================================================================
        while attempt < MAX_REPAIR_ATTEMPTS:
            attempt += 1
            yield _sse({"status": "generating_json", "attempt": attempt})

            attempt_text = ""
            try:
                async for token in stream_generation(
                    json_system_prompt,
                    current_user_message,
                    body.chat_history,
                    body.model,
                ):
                    attempt_text += token
                    yield _sse({"token": token})
            except Exception as e:  # noqa: BLE001
                yield _sse({"error": f"json generation failed: {e}"})
                yield _sse("[DONE]")
                return

            flow_json = fl.parse_flow_json(attempt_text)
            if flow_json is None:
                yield _sse({"status": "no_flow_json"})
                break

            # create the flow on first need
            if not flow_id:
                yield _sse({"status": "creating_flow"})
                name = fl.build_flow_name(body.user_message, body.flow_name)
                created = await aisensy_client.create_flow(name, body.flow_category)
                flow_id = created.get("id")
                if not flow_id:
                    yield _sse(
                        {
                            "error": "flow creation failed",
                            "detail": created.get("error_user_msg") or created,
                        }
                    )
                    break
                yield _sse({"flow_id": flow_id, "flow_name": name})

            # validate
            yield _sse({"status": "validating", "attempt": attempt})
            try:
                result = await aisensy_client.update_flow_json(flow_id, flow_json)
            except Exception as e:  # noqa: BLE001
                yield _sse({"status": "validator_unavailable", "detail": str(e)})
                final_flow_json = flow_json  # best effort
                break

            errors = result.get("validation_errors", [])
            yield _sse({"validation_errors": errors, "attempt": attempt})

            if not errors:
                final_flow_json = flow_json
                break

            if attempt >= MAX_REPAIR_ATTEMPTS:
                yield _sse({"status": "max_attempts_reached"})
                final_flow_json = flow_json  # return best effort
                break

            # repair: JSON only
            yield _sse({"status": "repairing", "attempt": attempt})
            current_user_message = fl.build_repair_prompt(flow_json, errors)
            body.chat_history = []

        # =====================================================================
        # PHASE 2 — generate the backend ONCE, against the final JSON
        # =====================================================================
        if final_flow_json is not None:
            yield _sse({"status": "generating_backend"})
            backend_user_message = build_backend_user_message(
                json.dumps(final_flow_json, indent=2)
            )
            try:
                async for token in stream_generation(
                    backend_system_prompt, backend_user_message, [], body.model
                ):
                    yield _sse({"token": token})
            except Exception as e:  # noqa: BLE001
                yield _sse({"error": f"backend generation failed: {e}"})

        # =====================================================================
        # preview + default endpoint
        # =====================================================================
        if flow_id:
            try:
                preview_url = await aisensy_client.get_preview(flow_id)
                if preview_url:
                    yield _sse({"preview_url": preview_url})
            except Exception as e:  # noqa: BLE001
                yield _sse({"status": "preview_unavailable", "detail": str(e)})

            service = fl.guess_service_name(final_flow_json, body.user_message)
            yield _sse({"endpoint_uri_default": fl.build_default_endpoint_uri(service)})

        yield _sse("[DONE]")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/flow/set-endpoint")
async def flow_set_endpoint(flow_id: str = Body(...), endpoint_uri: str = Body(...)):
    result = await aisensy_client.set_endpoint(flow_id, endpoint_uri)
    return {"ok": True, "result": result}


@app.post("/flow/publish")
async def flow_publish(flow_id: str = Body(...)):
    result = await aisensy_client.publish_flow(flow_id)
    success = result.get("success", True) and "error" not in result
    return {"ok": bool(success), "result": result}
