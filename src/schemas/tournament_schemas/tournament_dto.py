from datetime import datetime
from typing import List
from pydantic import BaseModel
from src.models.tournaments import FormatTournament, TypeTournament, StatusTournament
from src.schemas.organizer_schemas.organizer_dto import OrganizerDTO

class TournamentDTO(BaseModel):
    id: str
    name: str
    description: str
    type: TypeTournament
    status: StatusTournament
    format: FormatTournament
    number_participants: int
    url_image: str | None
    start: datetime
    end: datetime
    is_open: bool
    number_registered: int
    organizer: OrganizerDTO

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v,
        }

class ListTournamentDTO(BaseModel):
    tournaments: List[TournamentDTO]
    length: int