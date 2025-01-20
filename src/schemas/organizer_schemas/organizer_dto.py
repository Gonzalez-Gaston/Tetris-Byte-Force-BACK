from pydantic import BaseModel

class OrganizerDTO(BaseModel):
    id: str
    username: str
    url_image: str | None
    user_id: str

    class Config:
        from_attributes = True