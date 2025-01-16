from datetime import datetime, timezone
from sqlalchemy import Column, Enum as SQLAlchemyEnum
from sqlmodel import Relationship, SQLModel, Field
import uuid
from enum import Enum
from src.models.tournament_participants import TournamentParticipants
from typing import List

class TypeTournament(str, Enum):
    SIMPLE = "simple"
    DOUBLE = "doble"

class StatusTournament(str, Enum):
    PROXIMO = "proximo"
    CURSO = "en curso"
    FINALIZADO = "finalizado"

class Tournament(SQLModel, table=True):
    __tablename__ = 'tournaments'
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    name: str = Field(max_length=100)
    type: str = Field(sa_column=Column(SQLAlchemyEnum(TypeTournament)), default=TypeTournament.SIMPLE)
    status: str = Field(sa_column=Column(SQLAlchemyEnum(StatusTournament)), default=StatusTournament.PROXIMO)
    number_participants: int = Field()
    url_image: str | None = Field(default=None)
    start: datetime = Field()
    end: datetime = Field()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: str | None = Field()
    organizer_id: uuid.UUID = Field(foreign_key='organizers.id')
    participants: List["TournamentParticipants"] = Relationship(back_populates="tournament")
