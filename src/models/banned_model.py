import uuid
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, DateTime, String, func, case, cast, Boolean
from typing import Optional
from datetime import datetime, timezone


class UserBanned(SQLModel, table=True):
    __tablename__ = "users_banned"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    participant_id: str = Field(foreign_key="participants.id", index=True)
    tournament_id: str = Field(foreign_key='tournaments.id')