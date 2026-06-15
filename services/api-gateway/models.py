from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class FileType(str, Enum):
    pdf = "pdf"
    image = "image"
    text = "text"


class GeneratedFileType(str, Enum):
    flow_json = "flow_json"
    handler_py = "handler_py"


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class Session(SQLModel, table=True):
    __tablename__ = "sessions"  # type: ignore

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID
    title: str = Field(default="New Session")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    aisensy_flow_id: str | None = Field(default=None)
    endpoint_uri: str | None = Field(default=None)
    flow_status: str = Field(default="draft")  # "draft" | "published"
    flow_category: str | None = Field(default=None)


class Message(SQLModel, table=True):
    __tablename__ = "messages"  # type: ignore

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="sessions.id")
    role: MessageRole
    content: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class UploadedFile(SQLModel, table=True):
    __tablename__ = "uploaded_files"  # type: ignore

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="sessions.id")
    file_name: str
    file_path: str
    file_type: FileType
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class GeneratedFile(SQLModel, table=True):
    __tablename__ = "generated_files"  # type: ignore

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="sessions.id")
    message_id: UUID = Field(foreign_key="messages.id")
    file_type: GeneratedFileType
    file_path: str
    version: str = Field(default="7.3")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
