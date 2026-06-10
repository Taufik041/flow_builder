from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_register_proxied(client):
    with patch("routers.auth.httpx.AsyncClient") as mock:
        instance = AsyncMock()
        mock.return_value.__aenter__.return_value = instance
        instance.post.return_value.status_code = 200
        instance.post.return_value.json = lambda: {
            "access_token": "token",
            "token_type": "bearer",
        }
        response = await client.post(
            "/auth/register", json={"email": "test@test.com", "password": "test1234"}
        )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_proxied(client):
    with patch("routers.auth.httpx.AsyncClient") as mock:
        instance = AsyncMock()
        mock.return_value.__aenter__.return_value = instance
        instance.post.return_value.status_code = 200
        instance.post.return_value.json = lambda: {
            "access_token": "token",
            "token_type": "bearer",
        }
        response = await client.post(
            "/auth/login", json={"email": "test@test.com", "password": "test1234"}
        )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_protected_without_token(client):
    response = await client.get("/sessions/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_with_invalid_token(client):
    response = await client.get(
        "/sessions/", headers={"Authorization": "Bearer badtoken"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_with_valid_token(authed_client):
    response = await authed_client.get("/sessions/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_session(authed_client):
    response = await authed_client.post("/sessions/", json={"title": "Test Session"})
    assert response.status_code == 200
    assert response.json()["title"] == "Test Session"


@pytest.mark.asyncio
async def test_get_session(authed_client):
    create = await authed_client.post("/sessions/", json={"title": "Test Session"})
    session_id = create.json()["id"]
    response = await authed_client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["session"]["id"] == session_id
    assert response.json()["messages"] == []


@pytest.mark.asyncio
async def test_delete_session(authed_client):
    create = await authed_client.post("/sessions/", json={"title": "Test Session"})
    session_id = create.json()["id"]
    response = await authed_client.delete(f"/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["deleted"] == session_id


@pytest.mark.asyncio
async def test_cannot_access_other_users_session(authed_client, client):
    # create session as authed user
    create = await authed_client.post("/sessions/", json={"title": "Mine"})
    session_id = create.json()["id"]

    # try to access as different user
    from uuid import uuid4

    from jose import jwt

    other_token = jwt.encode(
        {"sub": str(uuid4()), "email": "other@test.com"},
        "test_secret_for_testing_only",
        algorithm="HS256",
    )
    from database import get_session
    from httpx import ASGITransport, AsyncClient
    from main import app
    from tests.conftest import override_get_session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {other_token}"},
    ) as other_client:
        response = await other_client.get(f"/sessions/{session_id}")
    assert response.status_code == 404
