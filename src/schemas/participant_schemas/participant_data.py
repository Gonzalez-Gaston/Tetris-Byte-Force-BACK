from pydantic import BaseModel

class ParticipantData(BaseModel):
    id: str
    username: str
    first_name: str
    last_name: str
    url_image: str | None
    user_id: str
    points: int | None
    win: int | None
    lose: int | None
    tournaments_win: int | None

    class Config:
        from_attributes = True