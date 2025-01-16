import uuid
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, DateTime, String, func, case, cast, Boolean
from typing import Optional
from datetime import datetime, timezone


class HistorialRefreshToken(SQLModel, table=True):
    __tablename__ = "HistorialRefreshToken"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    token: str = Field(max_length=500)
    refresh_token: str = Field(max_length=500)