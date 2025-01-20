from datetime import datetime
from typing import List
from pydantic import BaseModel
from src.models.tournaments import FormatTournament, TypeTournament, StatusTournament
from src.schemas.organizer_schemas.organizer_dto import OrganizerDTO
from src.schemas.participant_schemas.participant_dto import ParticipantDTO

class TournamentResponse(BaseModel):
    id: str
    name: str
    description: str
    type: TypeTournament
    status: StatusTournament
    format: FormatTournament
    number_participants: int
    data: str
    url_image: str | None
    start: datetime
    end: datetime
    is_open: bool
    number_registered: int
    organizer: OrganizerDTO
    list_participants: List[ParticipantDTO]

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v,
        }

class ListTournamentsResponse(BaseModel):
    tournaments: List[TournamentResponse]