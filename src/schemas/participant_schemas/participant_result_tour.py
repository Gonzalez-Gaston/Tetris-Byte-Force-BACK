from pydantic import BaseModel

class ParticipantResultTour(BaseModel):
    id: str
    username: str
    first_name: str
    last_name: str
    url_image: str | None
    user_id: str
    points: int | None
    win: int | None
    lose: int | None
    final_position: str | None

    class Config:
        from_attributes = True