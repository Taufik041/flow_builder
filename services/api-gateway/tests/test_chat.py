import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


def _make_gen_client(tokens: list[str], status_code: int = 200):
    """Mock httpx client yielding tokens then [DONE]."""

    async def fake_aiter_lines():
        for token in tokens:
            import json

            yield f"data: {json.dumps({'token': token})}"
        yield "data: [DONE]"

    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.aiter_lines = fake_aiter_lines
    mock_response.aclose = AsyncMock()

    mock_client = MagicMock()
    mock_client.build_request = MagicMock(return_value=MagicMock())
    mock_client.send = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()
    return mock_client


@pytest.mark.asyncio
async def test_chat_session_not_found(authed_client):
    from uuid import uuid4

    response = await authed_client.post(
        "/chat/",
        json={"session_id": str(uuid4()), "user_message": "hello"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


@pytest.mark.asyncio
async def test_chat_foreign_session(authed_client):
    """Session owned by user A returns 404 for user B."""
    create = await authed_client.post("/sessions/", json={"title": "Mine"})
    session_id = create.json()["id"]

    from datetime import datetime, timedelta, timezone
    from uuid import uuid4

    from jose import jwt

    other_token = jwt.encode(
        {
            "sub": str(uuid4()),
            "email": "other@test.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
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
        response = await other_client.post(
            "/chat/",
            json={"session_id": session_id, "user_message": "hello"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_chat_generation_service_down(authed_client):
    create = await authed_client.post("/sessions/", json={"title": "Test"})
    session_id = create.json()["id"]

    mock_client = MagicMock()
    mock_client.build_request = MagicMock(return_value=MagicMock())
    mock_client.send = AsyncMock(side_effect=httpx.ConnectError("refused"))
    mock_client.aclose = AsyncMock()

    with patch("routers.chat.httpx.AsyncClient", return_value=mock_client):
        response = await authed_client.post(
            "/chat/",
            json={"session_id": session_id, "user_message": "hello"},
        )

    assert response.status_code == 502
    assert "unavailable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_chat_happy_path_messages_persisted(authed_client):
    create = await authed_client.post("/sessions/", json={"title": "Chat test"})
    session_id = create.json()["id"]

    mock_client = _make_gen_client(["Hello", " world"])
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("routers.chat.httpx.AsyncClient", return_value=mock_client),
        patch("routers.chat.GENERATED_DIR", tmpdir),
    ):
        response = await authed_client.post(
            "/chat/",
            json={"session_id": session_id, "user_message": "Build a form"},
        )

    assert response.status_code == 200
    body = response.text
    assert '"token": "Hello"' in body
    assert '"token": " world"' in body
    assert "data: [DONE]" in body

    detail = await authed_client.get(f"/sessions/{session_id}")
    messages = detail.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Build a form"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hello world"


@pytest.mark.asyncio
async def test_chat_session_updated_at_bumped(authed_client):
    import time

    create = await authed_client.post("/sessions/", json={"title": "Bump test"})
    session = create.json()
    session_id = session["id"]
    original_updated_at = session["updated_at"]

    time.sleep(0.05)

    mock_client = _make_gen_client(["ok"])
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("routers.chat.httpx.AsyncClient", return_value=mock_client),
        patch("routers.chat.GENERATED_DIR", tmpdir),
    ):
        await authed_client.post(
            "/chat/",
            json={"session_id": session_id, "user_message": "ping"},
        )

    detail = await authed_client.get(f"/sessions/{session_id}")
    new_updated_at = detail.json()["session"]["updated_at"]
    assert new_updated_at != original_updated_at


@pytest.mark.asyncio
async def test_chat_saves_code_blocks(authed_client):
    create = await authed_client.post("/sessions/", json={"title": "Code test"})
    session_id = create.json()["id"]

    tokens = [
        "```json\n",
        '{"version": "7.3"}',
        "\n```\n",
        "```python\n",
        "def handler(): pass",
        "\n```",
    ]

    mock_client = _make_gen_client(tokens)
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("routers.chat.httpx.AsyncClient", return_value=mock_client),
        patch("routers.chat.GENERATED_DIR", tmpdir),
    ):
        await authed_client.post(
            "/chat/",
            json={"session_id": session_id, "user_message": "Generate"},
        )

        files_resp = await authed_client.get(f"/files/generated/{session_id}")
        assert files_resp.status_code == 200
        files = files_resp.json()
        assert len(files) == 2
        types = {f["file_type"] for f in files}
        assert "flow_json" in types
        assert "handler_py" in types


@pytest.mark.asyncio
async def test_chat_history_excludes_current_message(authed_client):
    """chat_history must not include the message just saved."""
    create = await authed_client.post("/sessions/", json={"title": "History test"})
    session_id = create.json()["id"]

    captured_payload: dict = {}

    async def fake_aiter_lines():
        import json

        yield f"data: {json.dumps({'token': 'ok'})}"
        yield "data: [DONE]"

    def capturing_build_request(method, url, **kwargs):
        captured_payload.update(kwargs.get("json", {}))
        return MagicMock()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.aiter_lines = fake_aiter_lines
    mock_response.aclose = AsyncMock()

    mock_client = MagicMock()
    mock_client.build_request = MagicMock(side_effect=capturing_build_request)
    mock_client.send = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()

    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("routers.chat.httpx.AsyncClient", return_value=mock_client),
        patch("routers.chat.GENERATED_DIR", tmpdir),
    ):
        await authed_client.post(
            "/chat/",
            json={"session_id": session_id, "user_message": "First message"},
        )

    assert captured_payload["chat_history"] == []
    assert captured_payload["user_message"] == "First message"
