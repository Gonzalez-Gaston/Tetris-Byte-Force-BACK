from pydantic import BaseModel

class ParticipantRanking(BaseModel):
    id: int
    username: str
    url_imgae: str
    user_id: str
    points: int
    win: int
    lose: int

    class Config:
        from_attributes = True