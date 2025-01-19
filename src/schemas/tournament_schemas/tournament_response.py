from datetime import datetime
from typing import List
from pydantic import BaseModel
from src.models.tournaments import TypeTournament, StatusTournament
from src.schemas.user_schema.user_full import UserFull


class TournamentResponse(BaseModel):
    id: str
    name: str
    description: str
    type: TypeTournament
    status: StatusTournament
    number_participants: int
    data: str
    url_image: str | None
    start: datetime
    end: datetime
    is_open: bool
    list_participants: List[UserFull] | None = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v,
        }