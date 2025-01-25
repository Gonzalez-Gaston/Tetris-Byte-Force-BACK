from pydantic import BaseModel

class ParticipantDTO(BaseModel):
    id: str
    username: str
    url_image: str | None
    user_id: str

    class Config:
        from_attributes = True

class TournamentParticipantDTO(BaseModel):
    id: str
    confirm: bool

    class Config:
        from_attributes = True

class ConjuntInscriptionDTO(BaseModel):
    participant: ParticipantDTO
    tournament_participant: TournamentParticipantDTO

    class Config:
        from_attributes = True