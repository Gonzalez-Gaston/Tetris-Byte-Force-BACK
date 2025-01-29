from pydantic import BaseModel

class OrganizerData(BaseModel):
    id: str
    username: str
    description: str | None
    url_image: str | None
    user_id: str
    tournaments_created: int | None

    class Config:
        from_attributes = True