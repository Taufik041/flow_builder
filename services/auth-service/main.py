from contextlib import asynccontextmanager

from auth import create_token, decode_token, hash_password, verify_password
from database import get_session, init_db
from fastapi import Depends, FastAPI, HTTPException
from models import User
from schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_session)):
    existing = await session.exec(select(User).where(User.email == body.email))
    if existing.first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_token(user.id, user.email)
    return TokenResponse(access_token=token)


@app.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(User).where(User.email == body.email))
    user = result.first()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user.id, user.email)
    return TokenResponse(access_token=token)


@app.post("/verify")
async def verify(token: str):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"user_id": payload["sub"], "email": payload["email"]}


@app.get("/me", response_model=UserResponse)
async def me(token: str, session: AsyncSession = Depends(get_session)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    result = await session.exec(select(User).where(User.email == payload["email"]))
    user = result.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(id=user.id, email=user.email)
