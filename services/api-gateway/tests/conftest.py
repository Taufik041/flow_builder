import os

os.environ["JWT_SECRET"] = "test_secret_for_testing_only"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_gateway.db"
from uuid import uuid4

import pytest_asyncio
from database import get_session
from httpx import ASGITransport, AsyncClient
from main import app
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

TEST_DATABASE_URL = "sqlite+aiosqlite:///./services/api-gateway/tests/test_gateway.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=SQLModelAsyncSession, expire_on_commit=False
)


async def override_get_session() -> SQLModelAsyncSession:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authed_client():
    app.dependency_overrides[get_session] = override_get_session
    from datetime import datetime, timedelta, timezone

    from jose import jwt

    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "email": "test@test.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        "test_secret_for_testing_only",
        algorithm="HS256",
    )
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
