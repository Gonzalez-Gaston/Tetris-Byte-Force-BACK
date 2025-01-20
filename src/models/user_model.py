from datetime import date, datetime, timezone
from enum import Enum
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Enum as SQLAlchemyEnum
import uuid

class RoleUser(str, Enum):
    PARTICIPANT = "participant"
    ORGANIZER = "organizer"

class User(SQLModel, table=True):
    __tablename__ = 'users'
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(max_length=50, unique=True)
    email: str = Field(max_length=50, unique=True, index=True)
    password_hash: str = Field(max_length=100)
    role: str = Field(sa_column=Column(SQLAlchemyEnum(RoleUser)), default=RoleUser.PARTICIPANT)
    is_active: bool = Field(default=False)
    token: str | None = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))