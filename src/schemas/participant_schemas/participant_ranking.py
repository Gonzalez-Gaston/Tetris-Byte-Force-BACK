from pydantic import BaseModel

class ParticipantRanking(BaseModel):
    id: str
    username: str
    url_imgae: str | None
    user_id: str
    points: int
    win: int
    lose: int
    tournaments_win: int | None

    class Config:
        from_attributes = True