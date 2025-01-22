from pydantic import BaseModel

class OrganizerBan(BaseModel):
    tournament_id: str
    participant_id: str