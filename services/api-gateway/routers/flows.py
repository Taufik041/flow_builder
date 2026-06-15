import os
from uuid import UUID

import httpx
from database import get_session as get_db_session
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from models import Session
from sqlalchemy.ext.asyncio.session import AsyncSession as SQLModelAsyncSession
from sqlmodel import select

router = APIRouter(prefix="/flows")

GENERATION_SERVICE_URL = os.getenv(
    "GENERATION_SERVICE_URL", "http://generation-service:8003"
)
_TIMEOUT = httpx.Timeout(30.0)


async def _require_session(
    session_id: UUID, user_id: UUID, db: SQLModelAsyncSession
) -> Session:
    result = await db.exec(select(Session).where(Session.id == session_id))
    session = result.first()
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}")
async def get_flow_state(
    session_id: UUID,
    request: Request,
    db: SQLModelAsyncSession = Depends(get_db_session),
):
    user_id = UUID(request.state.user_id)
    session = await _require_session(session_id, user_id, db)
    return {
        "session_id": str(session.id),
        "aisensy_flow_id": session.aisensy_flow_id,
        "endpoint_uri": session.endpoint_uri,
        "flow_status": session.flow_status,
        "flow_category": session.flow_category,
    }


@router.post("/{session_id}/endpoint")
async def set_flow_endpoint(
    session_id: UUID,
    request: Request,
    endpoint_uri: str = Body(..., embed=True),
    db: SQLModelAsyncSession = Depends(get_db_session),
):
    user_id = UUID(request.state.user_id)
    session = await _require_session(session_id, user_id, db)
    if not session.aisensy_flow_id:
        raise HTTPException(
            status_code=400, detail="No flow exists for this session yet"
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{GENERATION_SERVICE_URL}/flow/set-endpoint",
                json={
                    "flow_id": session.aisensy_flow_id,
                    "endpoint_uri": endpoint_uri,
                },
            )
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=502, detail="Generation service unavailable"
        ) from exc

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to set endpoint")

    session.endpoint_uri = endpoint_uri
    db.add(session)
    await db.commit()
    return {"ok": True, "endpoint_uri": endpoint_uri, "result": resp.json()}


@router.post("/{session_id}/publish")
async def publish_flow_endpoint(
    session_id: UUID,
    request: Request,
    db: SQLModelAsyncSession = Depends(get_db_session),
):
    user_id = UUID(request.state.user_id)
    session = await _require_session(session_id, user_id, db)
    if not session.aisensy_flow_id:
        raise HTTPException(
            status_code=400, detail="No flow exists for this session yet"
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{GENERATION_SERVICE_URL}/flow/publish",
                json={"flow_id": session.aisensy_flow_id},
            )
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=502, detail="Generation service unavailable"
        ) from exc

    result = resp.json()
    if resp.status_code != 200 or result.get("ok") is False:
        inner = result.get("result", {}) if isinstance(result, dict) else {}
        raise HTTPException(
            status_code=502,
            detail=inner.get("error_user_msg") or "Publish failed",
        )

    session.flow_status = "published"
    db.add(session)
    await db.commit()
    return {"ok": True, "flow_status": "published", "result": result}
