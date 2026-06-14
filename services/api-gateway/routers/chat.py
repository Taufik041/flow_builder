import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import httpx
from database import AsyncSessionLocal
from database import get_session as get_db_session
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from models import GeneratedFile, GeneratedFileType, Message, MessageRole, Session
from pydantic import BaseModel
from sqlalchemy.ext.asyncio.session import AsyncSession as SQLModelAsyncSession
from sqlmodel import select

router = APIRouter(prefix="/chat")

GENERATION_SERVICE_URL = os.getenv(
    "GENERATION_SERVICE_URL", "http://generation-service:8003"
)
GENERATED_DIR = os.getenv("GENERATED_DIR", "/generated")


class ChatRequest(BaseModel):
    session_id: UUID
    user_message: str
    extracted_text: str | None = None
    version: str = "7.3"
    top_k: int = 8
    model: str = "gpt-4o"


def _extract_code_blocks(text: str) -> tuple[str | None, str | None]:
    json_match = re.search(r"```json\s*([\s\S]*?)```", text)
    py_match = re.search(r"```python\s*([\s\S]*?)```", text)
    return (
        json_match.group(1).strip() if json_match else None,
        py_match.group(1).strip() if py_match else None,
    )


@router.post("/")
async def chat(
    request: Request,
    body: ChatRequest,
    db: SQLModelAsyncSession = Depends(get_db_session),
):
    user_id = UUID(request.state.user_id)

    # 1. Verify session ownership
    result = await db.exec(select(Session).where(Session.id == body.session_id))
    session = result.first()
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Save user message
    user_msg = Message(
        session_id=body.session_id,
        role=MessageRole.user,
        content=body.user_message,
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # 3. Load prior messages as chat_history (exclude the message just saved)
    history_result = await db.exec(
        select(Message)
        .where(Message.session_id == body.session_id)
        .where(Message.id != user_msg.id)
        .order_by(Message.created_at.asc())
    )
    chat_history = [
        {"role": msg.role.value, "content": msg.content} for msg in history_result.all()
    ]

    generate_payload = {
        "user_message": body.user_message,
        "extracted_text": body.extracted_text,
        "chat_history": chat_history,
        "version": body.version,
        "top_k": body.top_k,
        "model": body.model,
    }
    session_id = body.session_id
    version = body.version

    # 4. Open connection before returning StreamingResponse so we can 502 cleanly
    gen_client = httpx.AsyncClient(timeout=120.0)
    try:
        gen_req = gen_client.build_request(
            "POST",
            f"{GENERATION_SERVICE_URL}/generate",
            json=generate_payload,
        )
        gen_response = await gen_client.send(gen_req, stream=True)
    except httpx.ConnectError as exc:
        await gen_client.aclose()
        raise HTTPException(
            status_code=502, detail="Generation service unavailable"
        ) from exc

    if gen_response.status_code != 200:
        await gen_response.aclose()
        await gen_client.aclose()
        raise HTTPException(
            status_code=502,
            detail=f"Generation service returned {gen_response.status_code}",
        )

    async def event_stream():
        accumulated: list[str] = []
        try:
            async for line in gen_response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    token_data = json.loads(data)
                    if "token" in token_data:
                        accumulated.append(token_data["token"])
                        yield f"data: {json.dumps({'token': token_data['token']})}\n\n"
                    elif "error" in token_data:
                        yield f"data: {json.dumps({'error': token_data['error']})}\n\n"
                except json.JSONDecodeError:
                    pass
        except Exception as exc:  # noqa: BLE001
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            await gen_response.aclose()
            await gen_client.aclose()

        yield "data: [DONE]\n\n"

        full_text = "".join(accumulated)
        if not full_text:
            return

        # Post-stream persistence uses a fresh session (Depends session is closed)
        async with AsyncSessionLocal() as new_db:
            assistant_msg = Message(
                session_id=session_id,
                role=MessageRole.assistant,
                content=full_text,
            )
            new_db.add(assistant_msg)
            await new_db.commit()
            await new_db.refresh(assistant_msg)

            sess_result = await new_db.exec(
                select(Session).where(Session.id == session_id)
            )
            sess = sess_result.first()
            if sess:
                sess.updated_at = datetime.now(timezone.utc)
                new_db.add(sess)

            json_block, py_block = _extract_code_blocks(full_text)
            output_dir = Path(GENERATED_DIR) / str(session_id)
            output_dir.mkdir(parents=True, exist_ok=True)

            if json_block:
                json_path = output_dir / f"{assistant_msg.id}.json"
                json_path.write_text(json_block, encoding="utf-8")
                new_db.add(
                    GeneratedFile(
                        session_id=session_id,
                        message_id=assistant_msg.id,
                        file_type=GeneratedFileType.flow_json,
                        file_path=str(json_path),
                        version=version,
                    )
                )

            if py_block:
                py_path = output_dir / f"{assistant_msg.id}.py"
                py_path.write_text(py_block, encoding="utf-8")
                new_db.add(
                    GeneratedFile(
                        session_id=session_id,
                        message_id=assistant_msg.id,
                        file_type=GeneratedFileType.handler_py,
                        file_path=str(py_path),
                        version=version,
                    )
                )

            await new_db.commit()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
