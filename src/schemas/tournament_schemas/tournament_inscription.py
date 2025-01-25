from pydantic import BaseModel

from src.models.tournaments import FormatTournament, StatusTournament, TypeTournament

class TournamentInsc(BaseModel):
    id: str
    name: str
    type: TypeTournament
    status: StatusTournament
    format: FormatTournament
    number_participants: int
    is_open: bool

    class Config:
        from_attributes = True

class InscriptionDTO(BaseModel):
    id: str
    confirm: bool

    class Config:
        from_attributes = True

class TournamentInscription(BaseModel):
    tournament: TournamentInsc
    inscription: InscriptionDTO

    class Config:
        from_attributes = True