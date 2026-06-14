import os
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

from database import get_session as get_db_session
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from models import FileType, GeneratedFile, GeneratedFileType, Session, UploadedFile
from sqlalchemy.ext.asyncio.session import AsyncSession as SQLModelAsyncSession
from sqlmodel import select

router = APIRouter(prefix="/files")

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/uploads")
GENERATED_DIR = os.getenv("GENERATED_DIR", "/generated")

_ALLOWED_SUFFIXES: dict[str, FileType] = {
    ".pdf": FileType.pdf,
    ".png": FileType.image,
    ".jpg": FileType.image,
    ".jpeg": FileType.image,
}

_MEDIA_TYPES: dict[GeneratedFileType, str] = {
    GeneratedFileType.flow_json: "application/json",
    GeneratedFileType.handler_py: "text/x-python",
}


async def _require_session(
    session_id: UUID, user_id: UUID, db: SQLModelAsyncSession
) -> Session:
    result = await db.exec(select(Session).where(Session.id == session_id))
    session = result.first()
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/upload")
async def upload_file(
    request: Request,
    session_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: SQLModelAsyncSession = Depends(get_db_session),
):
    user_id = UUID(request.state.user_id)
    await _require_session(session_id, user_id, db)

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail="File type not allowed. Accepted: .pdf, .png, .jpg, .jpeg",
        )
    file_type = _ALLOWED_SUFFIXES[suffix]

    dest_dir = Path(UPLOAD_DIR) / str(session_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    dest_path = dest_dir / f"{uuid4()}_{file.filename}"
    dest_path.write_bytes(content)

    extracted_text: str | None = None
    if file_type == FileType.pdf:
        try:
            import pypdf

            reader = pypdf.PdfReader(BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
            extracted_text = text or None
        except Exception:  # noqa: BLE001
            extracted_text = None

    record = UploadedFile(
        session_id=session_id,
        file_name=file.filename or dest_path.name,
        file_path=str(dest_path),
        file_type=file_type,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return {
        "id": str(record.id),
        "file_name": record.file_name,
        "file_type": record.file_type.value,
        "extracted_text": extracted_text,
    }


@router.get("/generated/{session_id}")
async def list_generated_files(
    session_id: UUID,
    request: Request,
    db: SQLModelAsyncSession = Depends(get_db_session),
):
    user_id = UUID(request.state.user_id)
    await _require_session(session_id, user_id, db)

    result = await db.exec(
        select(GeneratedFile)
        .where(GeneratedFile.session_id == session_id)
        .order_by(GeneratedFile.created_at.asc())
    )
    return [
        {
            "id": str(f.id),
            "message_id": str(f.message_id),
            "file_type": f.file_type.value,
            "version": f.version,
            "created_at": f.created_at.isoformat(),
            "download_url": f"/files/generated/{session_id}/{f.id}/download",
        }
        for f in result.all()
    ]


@router.get("/generated/{session_id}/{file_id}/download")
async def download_generated_file(
    session_id: UUID,
    file_id: UUID,
    request: Request,
    db: SQLModelAsyncSession = Depends(get_db_session),
):
    user_id = UUID(request.state.user_id)
    await _require_session(session_id, user_id, db)

    result = await db.exec(
        select(GeneratedFile).where(
            GeneratedFile.id == file_id,
            GeneratedFile.session_id == session_id,
        )
    )
    gen_file = result.first()
    if not gen_file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(gen_file.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    media_type = _MEDIA_TYPES.get(gen_file.file_type, "application/octet-stream")
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={file_path.name}"},
    )
