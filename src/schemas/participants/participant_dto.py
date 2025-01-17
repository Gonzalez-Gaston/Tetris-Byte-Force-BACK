from pydantic import BaseModel
from src.schemas.user_schema.user_dto import UserDTO

class ParticipantDTO(BaseModel):
    id: str
    first_name: str
    last_name: str
    user: UserDTO