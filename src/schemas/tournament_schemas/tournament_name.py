from pydantic import BaseModel


class TournamentName(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True