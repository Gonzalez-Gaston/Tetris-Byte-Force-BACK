from pydantic import BaseModel
from src.models.organizer_model import Organizer
from src.models.participant_model import Participant
from src.models.user_model import User


class UserFull(BaseModel):
    user: User
    full: Participant | Organizer