from uuid import UUID

from database import get_session as get_db_session
from fastapi import APIRouter, Depends, HTTPException, Request
from models import Message, Session
from sqlalchemy.ext.asyncio.session import AsyncSession as SQLModelAsyncSession
from sqlmodel import select

router = APIRouter(prefix="/sessions")


@router.get("/")
async def list_sessions(
    request: Request, db: SQLModelAsyncSession = Depends(get_db_session)
):
    user_id = UUID(request.state.user_id)
    result = await db.exec(
        select(Session)
        .where(Session.user_id == user_id)
        .order_by(Session.updated_at.desc())
    )
    return result.all()


@router.post("/")
async def create_session(
    request: Request, body: dict, db: SQLModelAsyncSession = Depends(get_db_session)
):
    session = Session(
        user_id=UUID(request.state.user_id),
        title=body.get("title", "New Session"),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/{session_id}")
async def get_session(
    session_id: UUID,
    request: Request,
    db: SQLModelAsyncSession = Depends(get_db_session),
):
    result = await db.exec(select(Session).where(Session.id == session_id))
    session = result.first()
    if not session or session.user_id != UUID(request.state.user_id):
        raise HTTPException(status_code=404, detail="Session not found")

    messages_result = await db.exec(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    return {"session": session, "messages": messages_result.all()}


@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID,
    request: Request,
    db: SQLModelAsyncSession = Depends(get_db_session),
):
    result = await db.exec(select(Session).where(Session.id == session_id))
    session = result.first()
    if not session or session.user_id != UUID(request.state.user_id):
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return {"deleted": str(session_id)}
