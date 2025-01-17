from pydantic import BaseModel

class UserDTO(BaseModel):
    id: str
    username: str
    email: str
    url_image: str | None
