from datetime import datetime
from pydantic import BaseModel


class TournamentSocket(BaseModel):
    id: str
    name: str
    start: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v,
        }