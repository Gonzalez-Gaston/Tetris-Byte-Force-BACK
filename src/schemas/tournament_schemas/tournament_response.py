from datetime import datetime
from pydantic import BaseModel
from src.models.tournaments import TypeTournament, StatusTournament


class TournamentResponse(BaseModel):
    id: str
    name: str
    description: str
    type: TypeTournament
    status: StatusTournament
    number_participants: int
    url_image: str | None
    start: datetime
    end: datetime
    is_open: bool

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v,
        }