from datetime import date
from sqlmodel import Relationship, SQLModel, Field
import uuid
from typing import List

from src.models.tournament_participants import TournamentParticipants

class Participant(SQLModel, table=True):
    __tablename__ = 'participants'
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(max_length=50, unique=True)
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    date_of_birth: date = Field()
    url_image: str | None = Field(default=None)
    user_id: str = Field(foreign_key='users.id', index=True)
    tournaments: List["TournamentParticipants"] = Relationship(back_populates="participant")