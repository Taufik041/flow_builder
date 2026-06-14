import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_upload_rejects_bad_type(authed_client):
    create = await authed_client.post("/sessions/", json={"title": "Test"})
    session_id = create.json()["id"]

    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("routers.files.UPLOAD_DIR", tmpdir),
    ):
        response = await authed_client.post(
            "/files/upload",
            data={"session_id": session_id},
            files={"file": ("doc.txt", b"hello", "text/plain")},
        )

    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_image_no_extracted_text(authed_client):
    create = await authed_client.post("/sessions/", json={"title": "Test"})
    session_id = create.json()["id"]

    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("routers.files.UPLOAD_DIR", tmpdir),
    ):
        response = await authed_client.post(
            "/files/upload",
            data={"session_id": session_id},
            files={"file": ("form.png", b"\x89PNG\r\n", "image/png")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["file_name"] == "form.png"
    assert data["file_type"] == "image"
    assert data["extracted_text"] is None
    assert "id" in data


@pytest.mark.asyncio
async def test_upload_pdf_extracts_text(authed_client):
    create = await authed_client.post("/sessions/", json={"title": "Test"})
    session_id = create.json()["id"]

    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Extracted form content"
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("routers.files.UPLOAD_DIR", tmpdir),
        patch("pypdf.PdfReader", return_value=mock_reader),
    ):
        response = await authed_client.post(
            "/files/upload",
            data={"session_id": session_id},
            files={"file": ("form.pdf", b"%PDF-fake", "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == "pdf"
    assert data["extracted_text"] == "Extracted form content"


@pytest.mark.asyncio
async def test_upload_pdf_extraction_failure_returns_null(authed_client):
    create = await authed_client.post("/sessions/", json={"title": "Test"})
    session_id = create.json()["id"]

    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("routers.files.UPLOAD_DIR", tmpdir),
        patch("pypdf.PdfReader", side_effect=Exception("corrupt pdf")),
    ):
        response = await authed_client.post(
            "/files/upload",
            data={"session_id": session_id},
            files={"file": ("form.pdf", b"%PDF-corrupt", "application/pdf")},
        )

    assert response.status_code == 200
    assert response.json()["extracted_text"] is None


@pytest.mark.asyncio
async def test_upload_wrong_session(authed_client):
    """Uploading to another user's session returns 404."""
    from datetime import datetime, timedelta, timezone

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
    create = await authed_client.post("/sessions/", json={"title": "Mine"})
    session_id = create.json()["id"]

    from database import get_session
    from httpx import ASGITransport, AsyncClient
    from main import app
    from tests.conftest import override_get_session

    app.dependency_overrides[get_session] = override_get_session
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("routers.files.UPLOAD_DIR", tmpdir),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {other_token}"},
        ) as other_client:
            response = await other_client.post(
                "/files/upload",
                data={"session_id": session_id},
                files={"file": ("img.png", b"data", "image/png")},
            )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_generated_files_empty(authed_client):
    create = await authed_client.post("/sessions/", json={"title": "Test"})
    session_id = create.json()["id"]

    response = await authed_client.get(f"/files/generated/{session_id}")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_and_download_generated_files(authed_client):
    from uuid import UUID

    from models import GeneratedFile, GeneratedFileType, Message, MessageRole
    from tests.conftest import TestSessionLocal

    create = await authed_client.post("/sessions/", json={"title": "Test"})
    session_id_str = create.json()["id"]
    session_id = UUID(session_id_str)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / session_id_str
        output_dir.mkdir(parents=True, exist_ok=True)

        msg_id = uuid4()
        file_id = uuid4()
        json_content = '{"version": "7.3"}'
        json_path = output_dir / f"{file_id}.json"
        json_path.write_text(json_content)

        async with TestSessionLocal() as db:
            msg = Message(
                id=msg_id,
                session_id=session_id,
                role=MessageRole.assistant,
                content="response",
            )
            db.add(msg)
            gen_file = GeneratedFile(
                id=file_id,
                session_id=session_id,
                message_id=msg_id,
                file_type=GeneratedFileType.flow_json,
                file_path=str(json_path),
                version="7.3",
            )
            db.add(gen_file)
            await db.commit()

        with patch("routers.files.GENERATED_DIR", tmpdir):
            list_resp = await authed_client.get(f"/files/generated/{session_id_str}")
            assert list_resp.status_code == 200
            files = list_resp.json()
            assert len(files) == 1
            assert files[0]["file_type"] == "flow_json"
            assert files[0]["version"] == "7.3"
            download_url = files[0]["download_url"]

            dl_resp = await authed_client.get(download_url)
            assert dl_resp.status_code == 200
            assert dl_resp.text == json_content
            assert "attachment" in dl_resp.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_list_generated_wrong_session(authed_client):
    from datetime import datetime, timedelta, timezone

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
    create = await authed_client.post("/sessions/", json={"title": "Mine"})
    session_id = create.json()["id"]

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
        response = await other_client.get(f"/files/generated/{session_id}")
    assert response.status_code == 404
